import os
import time
import json
import numpy as np
import faiss
from typing import List, Dict, Union

class FaissEvaluator:
    def __init__(self, index_type: str, dimension: int, **kwargs):
        """
        Khởi tạo hệ thống FAISS Benchmark.
        :param index_type: 'FlatIP', 'IVFFlat', 'HNSWFlat', 'IVFPQ'
        :param dimension: Chiều vector (e.g. 512 cho SEARLE, 768 cho Pic2Word)
        """
        self.index_type = index_type
        self.dimension = dimension
        self.kwargs = kwargs
        self.index = self._build_index()

    def _build_index(self):
        if self.index_type == 'FlatIP':
            # Brute-force vét cạn - Inner Product (L2 normalized vectors -> Cosine Similarity)
            return faiss.IndexFlatIP(self.dimension)
            
        elif self.index_type == 'IVFFlat':
            nlist = self.kwargs.get('nlist', 256)
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            index.nprobe = self.kwargs.get('nprobe', 32)
            return index
            
        elif self.index_type == 'HNSWFlat':
            M = self.kwargs.get('M', 32)
            index = faiss.IndexHNSWFlat(self.dimension, M, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efSearch = self.kwargs.get('efSearch', 64)
            return index
            
        elif self.index_type == 'IVFPQ':
            nlist = self.kwargs.get('nlist', 256)
            m = self.kwargs.get('m', 8) # số lượng sub-quantizers
            bits_per_code = self.kwargs.get('bits_per_code', 8)
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, m, bits_per_code, faiss.METRIC_INNER_PRODUCT)
            index.nprobe = self.kwargs.get('nprobe', 32)
            return index
            
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")

    def add_gallery(self, gallery_features: np.ndarray):
        assert gallery_features.shape[1] == self.dimension
        assert gallery_features.dtype == np.float32, "FAISS strictly requires float32"
        
        # Train index if required (IVF, PQ models require training on data distribution)
        if not self.index.is_trained:
            print(f"Training {self.index_type} index...")
            t0 = time.perf_counter()
            self.index.train(gallery_features)
            t1 = time.perf_counter()
            print(f"Training completed in {t1-t0:.4f}s")
            
        print(f"Adding {gallery_features.shape[0]} vectors to {self.index_type}...")
        self.index.add(gallery_features)
        
    def search(self, query_features: np.ndarray, top_k: int = 50, batch_size: int = 256):
        assert query_features.dtype == np.float32
        
        # Tách riêng CPU thread limit để tránh đa luồng ngầm gây nhiễu QPS
        # faiss.omp_set_num_threads(1) có thể dùng nếu đo single-thread latency
        
        # 1. Warm-up phase
        warmup_queries = query_features[:min(100, len(query_features))]
        _ = self.index.search(warmup_queries, top_k)
        
        all_distances = []
        all_indices = []
        
        # 2. Benchmark phase (Isolated timer)
        start_time = time.perf_counter()
        
        for i in range(0, len(query_features), batch_size):
            batch_q = query_features[i : i + batch_size]
            distances, indices = self.index.search(batch_q, top_k)
            all_distances.append(distances)
            all_indices.append(indices)
            
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) / len(query_features) * 1000
        qps = len(query_features) / (end_time - start_time)
        
        return np.vstack(all_distances), np.vstack(all_indices), latency_ms, qps


def compute_fashioniq_cirr_recall(predicted_indices: np.ndarray, index_names: List[str], target_names: List[str], k_list=[1, 5, 10, 50]):
    """
    Tính Recall@K truyền thống cho FashionIQ và toàn thư viện CIRR.
    Mỗi query chỉ có 1 ground truth duy nhất.
    """
    sorted_index_names = np.array(index_names)[predicted_indices]
    
    # Check if target name is in the top-K retrieved names
    labels = (sorted_index_names == np.repeat(np.array(target_names), predicted_indices.shape[1]).reshape(len(target_names), -1))
    
    metrics = {}
    for k in k_list:
        metrics[f"recall_at{k}"] = (np.sum(labels[:, :k]) / len(labels)) * 100
        
    return metrics

def compute_cirr_subset_recall(predicted_indices: np.ndarray, index_names: List[str], target_names: List[str], group_members: List[List[str]], k_list=[1, 2, 3]):
    """
    Tính Subset Recall@K chỉ áp dụng cho CIRR.
    Chỉ tìm trong tập 6 bức ảnh nhiễu (group_members).
    """
    sorted_index_names = np.array(index_names)[predicted_indices]
    labels = (sorted_index_names == np.repeat(np.array(target_names), predicted_indices.shape[1]).reshape(len(target_names), -1))
    
    group_members_arr = np.array(group_members)
    # Mask out the images that are not in the subset
    group_mask = (sorted_index_names[:, :, None] == group_members_arr[:, None, :]).sum(-1).astype(bool)
    
    # Extract only the labels corresponding to the subset members, padding if some members are not in top-K
    group_labels_list = []
    for i in range(len(labels)):
        row_labels = labels[i][group_mask[i]]
        # Pad with False if not all group members were in the retrieved top-K
        padded = np.pad(row_labels, (0, max(0, group_members_arr.shape[1] - len(row_labels))), constant_values=False)
        group_labels_list.append(padded[:group_members_arr.shape[1]])
        
    group_labels = np.array(group_labels_list)
    
    metrics = {}
    for k in k_list:
        metrics[f"group_recall_at{k}"] = (np.sum(group_labels[:, :k]) / len(group_labels)) * 100
        
    return metrics

def compute_circo_map(predicted_indices: np.ndarray, index_names: List[str], gts_img_ids: List[List[str]], k_list=[5, 10, 25, 50]):
    """
    Tính mAP@K cho CIRCO (Multiple Ground Truths).
    Dựa trên source code CIRCO Evaluation Server.
    """
    sorted_index_names = np.array(index_names)[predicted_indices]
    
    ap_dict = {k: [] for k in k_list}
    recall_dict = {k: [] for k in k_list}
    
    for i, (predicted_names, gt_ids) in enumerate(zip(sorted_index_names, gts_img_ids)):
        gt_ids = np.array(gt_ids)[np.array(gt_ids) != '']
        
        # map_labels: array 1/0 showing if retrieved item is a GT
        map_labels = np.isin(predicted_names, gt_ids).astype(np.uint8)
        
        precisions = np.cumsum(map_labels) * map_labels
        precisions = precisions / np.arange(1, len(map_labels) + 1)
        
        target_name = gt_ids[0]
        single_gt_labels = (predicted_names == target_name)
        
        for k in k_list:
            ap_dict[k].append(np.sum(precisions[:k]) / min(len(gt_ids), k))
            recall_dict[k].append(np.sum(single_gt_labels[:k]))
            
    metrics = {}
    for k in k_list:
        metrics[f"map_at{k}"] = np.mean(ap_dict[k]) * 100
        metrics[f"recall_at{k}"] = np.mean(recall_dict[k]) * 100
        
    return metrics

use std::collections::HashMap;
use std::collections::VecDeque;
use std::hash::Hash;
use std::sync::{Arc, Mutex};

pub struct LRUCache<K, V> {
    capacity: usize,
    map: HashMap<K, V>,
    order: VecDeque<K>,
}

impl<K: Eq + Hash + Clone, V: Clone> LRUCache<K, V> {
    pub fn new(capacity: usize) -> Self {
        LRUCache {
            capacity,
            map: HashMap::new(),
            order: VecDeque::new(),
        }
    }

    pub fn get(&mut self, key: &K) -> Option<V> {
        if let Some(val) = self.map.get(key) {
            // Move to most recently used
            self.order.retain(|k| k != key);
            self.order.push_back(key.clone());
            Some(val.clone())
        } else {
            None
        }
    }

    pub fn put(&mut self, key: K, value: V) {
        if self.map.contains_key(&key) {
            self.map.insert(key.clone(), value);
            self.order.retain(|k| k != &key);
            self.order.push_back(key);
            return;
        }

        if self.map.len() >= self.capacity {
            if let Some(lru_key) = self.order.pop_front() {
                self.map.remove(&lru_key);
            }
        }

        self.map.insert(key.clone(), value);
        self.order.push_back(key);
    }

    pub fn len(&self) -> usize {
        self.map.len()
    }

    pub fn is_empty(&self) -> bool {
        self.map.is_empty()
    }
}

pub struct LRUCacheConcurrent<K, V> {
    inner: Mutex<LRUCache<K, V>>,
}

impl<K: Eq + Hash + Clone, V: Clone> LRUCacheConcurrent<K, V> {
    pub fn new(capacity: usize) -> Self {
        LRUCacheConcurrent {
            inner: Mutex::new(LRUCache::new(capacity)),
        }
    }

    pub fn get(&self, key: &K) -> Option<V> {
        self.inner.lock().unwrap().get(key)
    }

    pub fn put(&self, key: K, value: V) {
        self.inner.lock().unwrap().put(key, value);
    }
}

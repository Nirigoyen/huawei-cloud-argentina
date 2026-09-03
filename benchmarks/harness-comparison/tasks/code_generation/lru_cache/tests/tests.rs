use lru_cache::{LRUCache, LRUCacheConcurrent};

#[test]
fn test_basic_put_get() {
    let mut cache: LRUCache<i32, String> = LRUCache::new(2);
    cache.put(1, "one".to_string());
    cache.put(2, "two".to_string());
    assert_eq!(cache.get(&1), Some("one".to_string()));
    assert_eq!(cache.get(&2), Some("two".to_string()));
}

#[test]
fn test_eviction() {
    let mut cache: LRUCache<i32, i32> = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    cache.put(3, 30); // should evict key 1 (LRU)
    assert_eq!(cache.get(&1), None);
    assert_eq!(cache.get(&2), Some(20));
    assert_eq!(cache.get(&3), Some(30));
}

#[test]
fn test_get_updates_recency() {
    let mut cache: LRUCache<i32, i32> = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    // Access key 1, making key 2 the LRU
    assert_eq!(cache.get(&1), Some(10));
    cache.put(3, 30); // should evict key 2
    assert_eq!(cache.get(&1), Some(10));
    assert_eq!(cache.get(&2), None);
    assert_eq!(cache.get(&3), Some(30));
}

#[test]
fn test_update_existing_key() {
    let mut cache: LRUCache<i32, i32> = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(1, 100);
    assert_eq!(cache.get(&1), Some(100));
    assert_eq!(cache.len(), 1);
}

#[test]
fn test_len_and_empty() {
    let mut cache: LRUCache<i32, i32> = LRUCache::new(3);
    assert!(cache.is_empty());
    cache.put(1, 10);
    cache.put(2, 20);
    assert_eq!(cache.len(), 2);
    assert!(!cache.is_empty());
}

#[test]
fn test_capacity_one() {
    let mut cache: LRUCache<i32, i32> = LRUCache::new(1);
    cache.put(1, 10);
    cache.put(2, 20);
    assert_eq!(cache.get(&1), None);
    assert_eq!(cache.get(&2), Some(20));
    assert_eq!(cache.len(), 1);
}

#[test]
fn test_concurrent_access() {
    let cache: LRUCacheConcurrent<i32, i32> = LRUCacheConcurrent::new(100);
    cache.put(1, 10);
    cache.put(2, 20);

    let cache_clone = std::sync::Arc::new(cache);
    let cache1 = cache_clone.clone();
    let cache2 = cache_clone.clone();

    let h1 = std::thread::spawn(move || {
        cache1.put(3, 30);
        cache1.get(&1)
    });
    let h2 = std::thread::spawn(move || {
        cache2.put(4, 40);
        cache2.get(&2)
    });

    let r1 = h1.join().unwrap();
    let r2 = h2.join().unwrap();
    assert_eq!(r1, Some(10));
    assert_eq!(r2, Some(20));
}

#[test]
fn test_string_keys() {
    let mut cache: LRUCache<String, i32> = LRUCache::new(2);
    cache.put("a".to_string(), 1);
    cache.put("b".to_string(), 2);
    assert_eq!(cache.get(&"a".to_string()), Some(1));
    cache.put("c".to_string(), 3);
    assert_eq!(cache.get(&"b".to_string()), None);
    assert_eq!(cache.get(&"a".to_string()), Some(1));
    assert_eq!(cache.get(&"c".to_string()), Some(3));
}

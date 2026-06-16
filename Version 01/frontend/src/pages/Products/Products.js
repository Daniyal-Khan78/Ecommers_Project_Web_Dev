import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { productsAPI } from '../../api/products';
import ProductCard from '../../components/ProductCard/ProductCard';
import Spinner from '../../components/Spinner/Spinner';
import './Products.css';

const SORT_OPTIONS = [
  { value: 'newest',     label: 'Newest First' },
  { value: 'price_asc',  label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating',     label: 'Top Rated' },
];

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [products,    setProducts]    = useState([]);
  const [categories,  setCategories]  = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [pagination,  setPagination]  = useState({ count: 0, total_pages: 1 });
  const [filters,     setFilters]     = useState({
    q:          searchParams.get('q')          || '',
    category:   searchParams.get('category')   || '',
    min_price:  searchParams.get('min_price')  || '',
    max_price:  searchParams.get('max_price')  || '',
    on_sale:    searchParams.get('on_sale')    || '',
    sort:       searchParams.get('sort')       || 'newest',
    page:       searchParams.get('page')       || '1',
  });

  // Load products whenever filters change
  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });

      const data = await productsAPI.getProducts(params);
      if (data.success) {
        setProducts(data.data || []);
        setPagination({ count: data.count || 0, total_pages: data.total_pages || 1 });
      }
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  // Load categories once
  useEffect(() => {
    productsAPI.getCategories().then(d => { if (d.success) setCategories(d.data); });
  }, []);

  // Sync filters → URL
  useEffect(() => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: '1' }));
  };

  const clearFilters = () => {
    setFilters({ q: '', category: '', min_price: '', max_price: '', on_sale: '', sort: 'newest', page: '1' });
  };

  const hasActiveFilters = filters.q || filters.category || filters.min_price || filters.max_price || filters.on_sale;

  return (
    <div className="products-page">
      <div className="container">
        <div className="products-layout">

          {/* ── Sidebar Filters ─────────────────────────────── */}
          <aside className="filters-sidebar">
            <div className="filters-header">
              <h3>Filters</h3>
              {hasActiveFilters && (
                <button className="clear-filters-btn" onClick={clearFilters}>Clear All</button>
              )}
            </div>

            {/* Category */}
            <div className="filter-section">
              <h4>Category</h4>
              <div className="filter-options">
                <label className={`filter-option ${!filters.category ? 'active' : ''}`}>
                  <input type="radio" name="category" value="" checked={!filters.category}
                    onChange={() => updateFilter('category', '')} />
                  All Categories
                </label>
                {categories.map(cat => (
                  <label key={cat.id} className={`filter-option ${filters.category === String(cat.id) ? 'active' : ''}`}>
                    <input type="radio" name="category" value={cat.id}
                      checked={filters.category === String(cat.id)}
                      onChange={() => updateFilter('category', String(cat.id))} />
                    {cat.name} <span className="filter-count">({cat.product_count})</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div className="filter-section">
              <h4>Price Range</h4>
              <div className="price-inputs">
                <input type="number" placeholder="Min $" min="0" value={filters.min_price}
                  onChange={(e) => updateFilter('min_price', e.target.value)} />
                <span>–</span>
                <input type="number" placeholder="Max $" min="0" value={filters.max_price}
                  onChange={(e) => updateFilter('max_price', e.target.value)} />
              </div>
            </div>

            {/* On Sale */}
            <div className="filter-section">
              <h4>Deals</h4>
              <label className={`filter-option ${filters.on_sale === 'true' ? 'active' : ''}`}>
                <input type="checkbox" checked={filters.on_sale === 'true'}
                  onChange={(e) => updateFilter('on_sale', e.target.checked ? 'true' : '')} />
                🔥 On Sale Only
              </label>
            </div>
          </aside>

          {/* ── Products Area ────────────────────────────────── */}
          <div className="products-main">

            {/* Toolbar */}
            <div className="products-toolbar">
              <p className="results-count">
                {loading ? 'Loading...' : `${pagination.count} product${pagination.count !== 1 ? 's' : ''} found`}
                {filters.q && ` for "${filters.q}"`}
              </p>
              <div className="sort-wrapper">
                <label htmlFor="sort">Sort by:</label>
                <select id="sort" value={filters.sort}
                  onChange={(e) => updateFilter('sort', e.target.value)}>
                  {SORT_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Active filter chips */}
            {hasActiveFilters && (
              <div className="active-filters">
                {filters.q && <span className="filter-chip">Search: "{filters.q}" <button onClick={() => updateFilter('q', '')}>✕</button></span>}
                {filters.category && <span className="filter-chip">Category <button onClick={() => updateFilter('category', '')}>✕</button></span>}
                {filters.on_sale  && <span className="filter-chip">On Sale <button onClick={() => updateFilter('on_sale', '')}>✕</button></span>}
                {(filters.min_price || filters.max_price) && (
                  <span className="filter-chip">
                    Price: ${filters.min_price || '0'} – ${filters.max_price || '∞'}
                    <button onClick={() => { updateFilter('min_price', ''); updateFilter('max_price', ''); }}>✕</button>
                  </span>
                )}
              </div>
            )}

            {/* Grid */}
            {loading ? (
              <Spinner message="Loading products..." />
            ) : products.length === 0 ? (
              <div className="no-products">
                <p>🔍 No products found.</p>
                <button className="btn btn-secondary" onClick={clearFilters}>Clear Filters</button>
              </div>
            ) : (
              <div className="grid-4">
                {products.map(p => <ProductCard key={p.id} product={p} />)}
              </div>
            )}

            {/* Pagination */}
            {pagination.total_pages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-secondary"
                  disabled={filters.page === '1'}
                  onClick={() => updateFilter('page', String(Number(filters.page) - 1))}
                >← Prev</button>

                <span className="page-info">
                  Page {filters.page} of {pagination.total_pages}
                </span>

                <button
                  className="btn btn-secondary"
                  disabled={Number(filters.page) >= pagination.total_pages}
                  onClick={() => updateFilter('page', String(Number(filters.page) + 1))}
                >Next →</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Products;

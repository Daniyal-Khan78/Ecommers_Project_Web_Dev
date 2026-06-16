import React, { useEffect, useState, useCallback } from 'react';
import { productsAPI } from '../../../api/products';
import Spinner from '../../../components/Spinner/Spinner';
import { AdminNav } from '../Dashboard/Dashboard';
import '../Admin.css';

const EMPTY_FORM = {
  name: '', category: '', description: '',
  price: '', discount_price: '', stock: '', is_available: true,
};

const ManageProducts = () => {
  const [products,    setProducts]    = useState([]);
  const [categories,  setCategories]  = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [showModal,   setShowModal]   = useState(false);
  const [editProduct, setEditProduct] = useState(null); // null = create new
  const [form,        setForm]        = useState(EMPTY_FORM);
  const [saving,      setSaving]      = useState(false);
  const [formError,   setFormError]   = useState('');
  const [imageFile,   setImageFile]   = useState(null);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const [pd, cd] = await Promise.all([
        productsAPI.getAllProductsAdmin(),
        productsAPI.getCategories(),
      ]);
      if (pd.success) setProducts(pd.data || []);
      if (cd.success) setCategories(cd.data || []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  const openCreate = () => {
    setEditProduct(null);
    setForm(EMPTY_FORM);
    setFormError('');
    setImageFile(null);
    setShowModal(true);
  };

  const openEdit = (p) => {
    setEditProduct(p);
    setForm({
      name:           p.name,
      category:       p.category?.id || '',
      description:    p.description || '',
      price:          p.price,
      discount_price: p.discount_price || '',
      stock:          p.stock,
      is_available:   p.is_available,
    });
    setFormError('');
    setImageFile(null);
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');

    const payload = {
      name:        form.name,
      description: form.description,
      price:       parseFloat(form.price),
      stock:       parseInt(form.stock, 10),
      is_available: form.is_available,
    };
    if (form.category)       payload.category       = parseInt(form.category, 10);
    if (form.discount_price) payload.discount_price = parseFloat(form.discount_price);

    try {
      let data;
      if (editProduct) {
        data = await productsAPI.updateProduct(editProduct.id, payload);
      } else {
        data = await productsAPI.createProduct(payload);
      }

      if (!data.success) {
        const errText = data.message || Object.values(data.errors || {})[0]?.[0] || 'Save failed.';
        setFormError(errText);
        setSaving(false);
        return;
      }

      // Upload image if provided
      if (imageFile) {
        const fd = new FormData();
        fd.append('images', imageFile);
        await productsAPI.uploadImages(data.data.id, fd);
      }

      setShowModal(false);
      loadProducts();
    } catch {
      setFormError('An error occurred. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this product? This cannot be undone.')) return;
    const data = await productsAPI.deleteProduct(id);
    if (data.success) setProducts(prev => prev.filter(p => p.id !== id));
  };

  const toggleAvailable = async (p) => {
    const data = await productsAPI.updateProduct(p.id, { is_available: !p.is_available });
    if (data.success) setProducts(prev => prev.map(x => x.id === p.id ? data.data : x));
  };

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Manage Products</h1>
        <p className="admin-subtitle">Create, edit, and manage your product catalogue.</p>
        <AdminNav active="products" />

        <div className="admin-section">
          <div className="admin-section-header">
            <h2>All Products ({products.length})</h2>
            <button className="btn btn-primary" onClick={openCreate} style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
              + Add Product
            </button>
          </div>

          {loading ? (
            <div style={{ padding: '2rem' }}><Spinner /></div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Image</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Available</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => (
                    <tr key={p.id}>
                      <td>
                        {p.primary_image_url ? (
                          <img src={p.primary_image_url} alt={p.name} className="admin-product-img" />
                        ) : (
                          <div className="admin-product-img" style={{ background:'var(--light-gray)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'1.25rem' }}>🛍️</div>
                        )}
                      </td>
                      <td style={{ fontWeight: 600 }}>{p.name}</td>
                      <td>{p.category?.name || '—'}</td>
                      <td>
                        ${parseFloat(p.effective_price).toFixed(2)}
                        {p.is_on_sale && <span style={{ color:'var(--success)', fontSize:'0.75rem', marginLeft:'0.3rem' }}>SALE</span>}
                      </td>
                      <td>{p.stock}</td>
                      <td>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={p.is_available}
                            onChange={() => toggleAvailable(p)}
                          />
                          <span className="toggle-slider" />
                        </label>
                      </td>
                      <td style={{ display:'flex', gap:'0.4rem' }}>
                        <button className="admin-action-btn" onClick={() => openEdit(p)}>Edit</button>
                        <button className="admin-action-btn danger" onClick={() => handleDelete(p.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Create/Edit Modal */}
        {showModal && (
          <div className="admin-modal-overlay" onClick={() => setShowModal(false)}>
            <div className="admin-modal" onClick={e => e.stopPropagation()}>
              <h2>{editProduct ? 'Edit Product' : 'Create Product'}</h2>
              <form onSubmit={handleSave}>
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input className="form-control" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select className="form-control" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                    <option value="">— No category —</option>
                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-control" rows={3} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                </div>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Price ($) *</label>
                    <input className="form-control" type="number" step="0.01" min="0.01" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Discount Price ($)</label>
                    <input className="form-control" type="number" step="0.01" min="0" value={form.discount_price} onChange={e => setForm(f => ({ ...f, discount_price: e.target.value }))} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Stock *</label>
                  <input className="form-control" type="number" min="0" value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} required />
                </div>
                {!editProduct && (
                  <div className="form-group">
                    <label className="form-label">Product Image</label>
                    <input type="file" accept="image/*" className="form-control" onChange={e => setImageFile(e.target.files[0])} />
                  </div>
                )}
                <div className="form-group" style={{ display:'flex', alignItems:'center', gap:'0.5rem' }}>
                  <input type="checkbox" id="is_available" checked={form.is_available} onChange={e => setForm(f => ({ ...f, is_available: e.target.checked }))} />
                  <label htmlFor="is_available" className="form-label" style={{ margin:0 }}>Available for sale</label>
                </div>
                {formError && <div style={{ color:'var(--danger)', fontSize:'0.875rem', marginTop:'0.5rem' }}>{formError}</div>}
                <div className="admin-modal-footer">
                  <button type="button" className="btn" style={{ background:'var(--light-gray)', color:'var(--dark)', border:'1px solid var(--border)' }} onClick={() => setShowModal(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ManageProducts;

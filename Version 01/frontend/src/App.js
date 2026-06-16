import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Layout components
import Navbar  from './components/Navbar/Navbar';
import Footer  from './components/Footer/Footer';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';

// Public pages
import Home          from './pages/Home/Home';
import Login         from './pages/Login/Login';
import Register      from './pages/Register/Register';
import Products      from './pages/Products/Products';
import ProductDetail from './pages/ProductDetail/ProductDetail';
import VerifyEmail   from './pages/VerifyEmail/VerifyEmail';
import NotFound      from './pages/NotFound/NotFound';

// Protected customer pages
import Cart       from './pages/Cart/Cart';
import Wishlist   from './pages/Wishlist/Wishlist';
import Checkout   from './pages/Checkout/Checkout';
import Orders     from './pages/Orders/Orders';
import OrderDetail from './pages/Orders/OrderDetail';
import Profile    from './pages/Profile/Profile';

// Protected admin pages
import AdminDashboard  from './pages/Admin/Dashboard/Dashboard';
import ManageProducts  from './pages/Admin/ManageProducts/ManageProducts';
import ManageOrders    from './pages/Admin/ManageOrders/ManageOrders';
import ManageUsers     from './pages/Admin/ManageUsers/ManageUsers';
import Analytics       from './pages/Admin/Analytics/Analytics';

function App() {
  return (
    <Router>
      <div className="app-wrapper">
        <Navbar />

        <main className="main-content">
          <Routes>

            {/* ── Public Routes ─────────────────────────────── */}
            <Route path="/"             element={<Home />} />
            <Route path="/login"        element={<Login />} />
            <Route path="/register"     element={<Register />} />
            <Route path="/products"     element={<Products />} />
            <Route path="/products/:id"        element={<ProductDetail />} />
            <Route path="/verify-email/:token" element={<VerifyEmail />} />

            {/* ── Protected Customer Routes ──────────────────── */}
            <Route path="/cart" element={
              <ProtectedRoute><Cart /></ProtectedRoute>
            } />
            <Route path="/wishlist" element={
              <ProtectedRoute><Wishlist /></ProtectedRoute>
            } />
            <Route path="/checkout" element={
              <ProtectedRoute><Checkout /></ProtectedRoute>
            } />
            <Route path="/orders" element={
              <ProtectedRoute><Orders /></ProtectedRoute>
            } />
            <Route path="/orders/:id" element={
              <ProtectedRoute><OrderDetail /></ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute><Profile /></ProtectedRoute>
            } />

            {/* ── Protected Admin Routes ─────────────────────── */}
            <Route path="/admin" element={
              <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
            } />
            <Route path="/admin/products" element={
              <ProtectedRoute adminOnly><ManageProducts /></ProtectedRoute>
            } />
            <Route path="/admin/orders" element={
              <ProtectedRoute adminOnly><ManageOrders /></ProtectedRoute>
            } />
            <Route path="/admin/users" element={
              <ProtectedRoute adminOnly><ManageUsers /></ProtectedRoute>
            } />
            <Route path="/admin/analytics" element={
              <ProtectedRoute adminOnly><Analytics /></ProtectedRoute>
            } />

            {/* ── 404 ───────────────────────────────────────── */}
            <Route path="*" element={<NotFound />} />

          </Routes>
        </main>

        <Footer />
      </div>
    </Router>
  );
}

export default App;

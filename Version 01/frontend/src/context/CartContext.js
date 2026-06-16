import React, { createContext, useContext, useState, useCallback } from 'react';

// CartContext stores the cart item count for the Navbar badge (the red number).
// The full cart data lives in the Cart page — we only need the count globally.
const CartContext = createContext(null);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) throw new Error('useCart must be used inside a CartProvider');
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartCount, setCartCount] = useState(0);

  // Called whenever the cart changes (add, remove, update, clear)
  // Pass the new total item count from the cart API response
  const updateCartCount = useCallback((count) => {
    setCartCount(count);
  }, []);

  const clearCartCount = useCallback(() => {
    setCartCount(0);
  }, []);

  return (
    <CartContext.Provider value={{ cartCount, updateCartCount, clearCartCount }}>
      {children}
    </CartContext.Provider>
  );
};

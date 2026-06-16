# ShopNest — Claude Code Session Handoff Document

**Generated:** 2026-06-07  
**Project root:** `C:\Users\PC\Pictures\Web Dev Project\shopnest\`  
**Git commits:** 9 commits on `master`  
**Status:** Phases 1–11 Part 2 complete (all frontend pages built). Resume at **Phase 13 / Phase 14 testing**.

---

## 1. Project Overview

Full-stack e-commerce web application built as a university course project.

- **Course:** Web Application Development
- **Requirement:** Register + Login + CRUD + API Integration + DB + Responsive Design
- **Selected idea:** E-Commerce Website (option 4 from approved list)
- **Group policy:** Max 2 students; individual work allowed
- **Submission:** GitHub link + screenshots + group member names

---

## 2. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React JS | 18.x (CRA) |
| Styling | CSS3 (custom, no Tailwind) | — |
| HTTP | Fetch API (no Axios) | — |
| Routing | React Router DOM | v6 |
| Backend | Django | 5.2.15 |
| API | Django REST Framework (DRF) | 3.17.1 |
| Auth | SimpleJWT (JWT tokens) | 5.5.1 |
| Database | SQLite | (via Django ORM) |
| Payments | Stripe | 15.2.0 |
| Images | Pillow | 12.2.0 |
| CORS | django-cors-headers | 4.9.0 |
| Version Control | Git & GitHub | — |

**No Redux. No Axios. No Tailwind. No PostgreSQL.** Use only what is listed above.

---

## 3. How to Start Both Servers

```powershell
# Terminal 1 — Django (port 8000)
cd "C:\Users\PC\Pictures\Web Dev Project\shopnest\backend"
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2 — React (port 3000)
cd "C:\Users\PC\Pictures\Web Dev Project\shopnest\frontend"
npm start
```

**Django admin:** http://localhost:8000/admin/  
**Username:** `admin` | **Password:** `Admin@123456`

**Test customer:** `john@shopnest.com` | `SecurePass@123`

---

## 4. Complete Folder Structure

```
shopnest/
├── .git/
├── .gitignore
├── README.md
├── HANDOFF.md                          ← this file
│
├── backend/                            ← Django project
│   ├── venv/                           ← Python venv (NOT committed)
│   ├── manage.py
│   ├── requirements.txt
│   ├── db.sqlite3                      ← database (NOT committed)
│   ├── media/                          ← uploaded images (NOT committed)
│   │
│   ├── backend/
│   │   ├── settings.py
│   │   └── urls.py
│   │
│   ├── utils/
│   │   ├── responses.py
│   │   ├── exceptions.py
│   │   ├── permissions.py
│   │   └── notifications.py
│   │
│   ├── users/
│   ├── products/
│   ├── cart/
│   ├── wishlist/
│   ├── orders/
│   └── notifications/
│       ├── models.py
│       ├── serializers.py              ← NEW — NotificationSerializer
│       ├── views.py                    ← NEW — NotificationListView, MarkAllReadView
│       └── urls.py                     ← FIXED — routes registered
│
└── frontend/                           ← React app (CRA)
    └── src/
        ├── App.js                      ← Router (all routes wired)
        ├── App.css                     ← global CSS + .form-control + .form-label aliases
        ├── api/                        ← all API modules
        ├── context/                    ← AuthContext, CartContext
        ├── components/
        │   ├── Navbar/                 ← UPDATED: cart count init on load + bell icon + notif dropdown
        │   ├── Footer/
        │   ├── ProductCard/
        │   ├── Spinner/
        │   └── ProtectedRoute/
        └── pages/
            ├── Home/                   ← DONE
            ├── Login/                  ← DONE
            ├── Register/               ← DONE
            ├── Products/               ← DONE
            ├── NotFound/               ← DONE
            ├── ProductDetail/          ← DONE (gallery, price, qty, wishlist, related products, breadcrumb)
            ├── Cart/                   ← DONE (item list, qty controls, order summary, empty state)
            ├── Wishlist/               ← DONE (grid, move-to-cart, remove)
            ├── Checkout/               ← DONE (2-step: shipping + Stripe CardElement + COD)
            ├── Orders/                 ← DONE (list with status tabs)
            │   └── OrderDetail.js      ← DONE (items, shipping, payment, cancel button)
            ├── Profile/                ← DONE (edit info, avatar upload, email verify, change password)
            └── Admin/
                ├── Admin.css           ← NEW shared admin styles
                ├── Dashboard/          ← DONE (stats cards, recent orders, quick links)
                ├── ManageProducts/     ← DONE (table, create/edit modal, delete, toggle available)
                ├── ManageOrders/       ← DONE (table, status filter, inline status update dropdown)
                ├── ManageUsers/        ← DONE (table, toggle is_active/is_admin)
                └── Analytics/          ← DONE (CSS bar chart, status bars, summary stats)
```

---

## 5. Database Schema (All 12 Models)

*(Unchanged — see previous handoff for full schema)*

Key models:
- `users_user` — extends AbstractUser, `profile_image_url` returned by serializer
- `products_product` — `effective_price`, `is_on_sale`, `primary_image` @properties
- `cart_cart` / `cart_cartitem` — auto-created via signal; `subtotal` @property
- `orders_order` — status: pending|confirmed|shipped|delivered|cancelled
- `orders_payment` — method: stripe|cod; status: pending|completed|failed|refunded
- `notifications_notification` — type: order|payment|system|promo|wishlist

---

## 6. All API Endpoints

*(All unchanged — fully implemented)*

**Base URL:** `http://localhost:8000`  
**Auth header:** `Authorization: Bearer <access_token>`

### Notifications — `/api/notifications/` ← NOW FULLY WORKING
```
GET    /       Auth   → {notifications: [...], unread_count: N}
PUT    /read/  Auth   → mark all as read
```

*(All other endpoints unchanged — see previous handoff)*

---

## 7. Implemented Features

### Backend (100% Complete)
*(All items from previous handoff, plus:)*
- [x] Notifications API — `GET /api/notifications/` and `PUT /api/notifications/read/` now implemented

### Frontend (100% Complete — Phase 11 Part 2 done)
- [x] All items from Phase 11 Part 1 (Auth, CartContext, API layer, routing, Navbar, etc.)
- [x] **Navbar** — cart count initialised from API on login/refresh; notification bell with unread badge + dropdown
- [x] **ProductDetail** — image gallery (primary + thumbnails), price + discount badge, qty selector, add-to-cart, wishlist toggle (checks API on load), description, related products, breadcrumb
- [x] **Cart** — item list with product image/name/qty controls/remove, order summary sidebar (subtotal/savings/total), "Proceed to Checkout" CTA, empty state, updates CartContext
- [x] **Checkout** — step 1: shipping address + payment method (card/COD); step 2: Stripe `<Elements>` + `<CardElement>` for card payments; handles 3D Secure flow; COD goes straight to order; clears cart count on success
- [x] **Orders** — list with status tab filter; click → OrderDetail
- [x] **OrderDetail** — items table (snapshot prices), shipping address, payment info, cancel button (pending/confirmed only)
- [x] **Wishlist** — product grid, move-to-cart, remove button, empty state
- [x] **Profile** — personal info edit, avatar upload, email verification status + resend, change password
- [x] **Admin Dashboard** — stats cards (orders/revenue/products/users), recent orders table, quick-links grid
- [x] **Admin ManageProducts** — table of all products (including unavailable), create/edit modal, delete with confirm, toggle is_available switch, image upload on create
- [x] **Admin ManageOrders** — table with status filter, inline status update `<select>` per row
- [x] **Admin ManageUsers** — table with toggle is_active/is_admin per user
- [x] **Admin Analytics** — CSS bar chart (daily revenue last 30 days), status bar chart, summary stats cards

---

## 8. Remaining Tasks

### Immediate (before submission)

**Step 1 — Add real Stripe test keys to `backend/backend/settings.py`**
```python
STRIPE_SECRET_KEY      = 'sk_test_YOUR_REAL_KEY_HERE'
STRIPE_PUBLISHABLE_KEY = 'pk_test_YOUR_REAL_KEY_HERE'
STRIPE_WEBHOOK_SECRET  = 'whsec_YOUR_WEBHOOK_SECRET'
```
Get keys from: https://dashboard.stripe.com/test/apikeys

**Step 2 — Phase 15: AI Recommendation System (optional)**
- Populate `Recommendation` model based on user order history
- Write management command: `python manage.py generate_recommendations`
- Frontend `Home` page already shows "Recommended for You" section — it calls `GET /api/products/recommendations/` which falls back to top-rated if no recommendations exist

**Step 3 — Phase 16: Basic Tests**
- Django: write `tests.py` in each app (at minimum: auth register/login, product list, cart add)
- React: basic smoke tests with `@testing-library/react`

**Step 4 — Phase 17: Deployment + GitHub**
```bash
# Change git identity before pushing
git config user.name "Your Name"
git config user.email "your@email.com"

# Push to GitHub
git remote add origin https://github.com/<username>/shopnest.git
git push -u origin master
```
- Take screenshots of every feature
- Update README with setup instructions
- Submit GitHub link + screenshots + student names

---

## 9. Important Design Decisions

*(All preserved from previous handoff)*

1. **`AUTH_USER_MODEL = 'users.User'`** — must be set before first migration
2. **Standard response envelope** — `{success, message, data?, errors?}` on every response
3. **Price snapshot in `OrderItem.price`** — never changes after order is placed
4. **`transaction.atomic()` + `select_for_update()`** in `PlaceOrderView`
5. **`F('stock') - quantity`** for stock decrement
6. **Cart auto-created via signal** — `users/signals.py`
7. **`unique_together` on CartItem and Wishlist**
8. **Stripe card stays in browser** — card numbers never touch Django
9. **`featured/` URL before `<int:pk>/`** in products/urls.py
10. **Notification helper** — lazy import to avoid circular imports
11. **CSS design system** — all CSS variables in `:root` in `App.css`
12. **`apiFetch` auto-refresh** — retries on 401 with refreshed token
13. **`AdminNav` component** — exported from `Dashboard/Dashboard.js`, imported in all other admin pages for consistent navigation
14. **`form-control` / `form-label`** — CSS utility aliases added to `App.css` (used by Profile, Checkout, Admin pages)

---

## 10. Known Issues

| # | Location | Issue | Severity |
|---|---|---|---|
| 1 | `backend/backend/settings.py` | `STRIPE_SECRET_KEY` is placeholder `sk_test_...` — payments won't work | High |
| 2 | Git identity | Committed as `student / student@example.com` — change before submitting | Low |
| 3 | `STATIC_ROOT` | Not set; `urls.py` has a guard | Low |
| 4 | AI Recommendations | `Recommendation` model exists; no algorithm writes to it yet (falls back to top-rated) | Low |
| 5 | Email backend | Console backend in dev — emails print to terminal | Acceptable for dev |
| 6 | `ProductCard` wishlist | `wishlisted` state starts `false` on mount (no initial check) — fixed in `ProductDetail` but not in the card component on listing pages | Low |
| 7 | Admin image upload | Only supports upload at product creation; editing an existing product's images requires navigating to Django admin | Low |

---

## 11. Checkout Flow (Stripe)

```
1. User fills: shipping_address, payment_method (stripe|cod), notes
2. POST /api/orders/create/ → { id: orderId, total_amount, ... }
3a. If COD → navigate /orders/{orderId}
3b. If Stripe:
   POST /api/payments/create-intent/ { order_id } → { client_secret, publishable_key }
   loadStripe(publishable_key) → <Elements stripe={stripePromise}>
   User enters card in <CardElement>
   stripe.confirmCardPayment(client_secret, { payment_method: { card: cardElement } })
   On success → POST /api/payments/confirm/ { order_id, payment_intent_id }
   → navigate /orders/{orderId}
```

---

## 12. Git State

```
Branch: master
Commits: 9 (no new commits added this session — all changes are working tree)

29fae56  Phase 11 Part 1: React frontend foundation
bc7b0f0  Phase 10: Stripe payment integration
c4e8065  Phase 9: Complete order management system
53c2d89  Phase 7 & 8: Cart and Wishlist APIs
3759a54  Phase 5 & 6: Product and Category management APIs
30e370d  Phase 4: Complete authentication system
a6c63ed  Phase 3: Django backend infrastructure setup
c1790b7  Phase 2: Complete database design — 12 models
0f88764  Phase 1: Project setup — Django + React skeleton
```

**All Phase 11 Part 2 changes are uncommitted.** Commit before pushing:
```bash
git add .
git commit -m "Phase 11 Part 2: Complete frontend — all customer + admin pages"
```

No remote set yet:
```bash
git remote add origin https://github.com/<username>/shopnest.git
git push -u origin master
```

---

## 13. Seeded Test Data

| Type | Data |
|---|---|
| Admin user | username: `admin`, email: `admin@shopnest.com`, password: `Admin@123456` |
| Customer | username: `johndoe`, email: `john@shopnest.com`, password: `SecurePass@123` |
| Test user | username: `testuser`, email: `test@test.com`, password: `Test@123` |
| Categories | Electronics, Clothing, Books, Home & Garden, Sports |
| Products | iPhone 15 Pro, Samsung Galaxy S24, MacBook Air M3, Nike Air Max 270, Levi 501 Jeans, Python Crash Course, Garden Tool Set, Yoga Mat Pro |
| Orders | Order #1 (john, confirmed, $1827.98, cod), Order #2 (john, pending, stripe) |

---

*End of handoff document. All customer and admin frontend pages are complete. Next: add real Stripe keys, run both servers, test the golden path (browse → add to cart → checkout → view order), then push to GitHub.*

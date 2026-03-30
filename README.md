# SplitEase

A full-stack expense-splitting application that helps groups track shared expenses, settle balances, and manage personal finances. The project consists of a Django web application and a React Native mobile app backed by the same REST API.

---

## Overview

SplitEase allows users to create group trips, record shared expenses, track who owes whom, and settle debts with minimal transactions. It also includes personal expense tracking with category breakdowns and a friend system for adding co-travelers.

**Live Web App:** https://splitease-1vlc.onrender.com
_(Currently hosted on Render. Migration to DigitalOcean is planned.)_

---

## Repository Structure

```
SplitEaseCode/       Django backend + web frontend (this repository)
SplitEaseApp/        React Native mobile app (Expo)
```

---

## Tech Stack

### Backend / Web
- Python 3.13, Django 6.0.3
- Django REST Framework 3.15.2
- JWT authentication via `djangorestframework-simplejwt`
- PostgreSQL (production), SQLite (local development)
- Gunicorn + WhiteNoise for production serving
- Deployed on Render via `render.yaml`

### Mobile App
- React Native 0.81.5, React 19.1.0
- Expo SDK 54
- React Navigation 7 (bottom tabs + native stack)
- Axios for API requests
- AsyncStorage for token persistence
- Built and distributed via EAS (Expo Application Services)
- Android APK available for direct installation

---

## Features

### Trip Management
- Create group trips and invite friends as members
- View all members and their balances within a trip
- Delete trips (creator only)

### Expense Tracking
- Add expenses with description, date, amount, and who paid
- Split mode: equal split across members or custom amounts per member
- Delete expenses you added
- Full expense history per trip

### Settlement
- Automatic balance calculation across all trip expenses
- Optimized settlement suggestions to minimize the number of transactions
- Record manual payments between members
- Settlement history per trip

### Personal Expenses
- Log personal expenses with 9 categories: Food, Transport, Shopping, Entertainment, Health, Utilities, Rent, Travel, Other
- Category-wise totals and monthly breakdowns for the last 12 months
- Delete individual personal expense entries

### Friend System
- Search for users by username
- Send, accept, and decline friend requests
- Remove existing friends
- Only friends can be added as trip members

### Authentication
- User registration with email, first name, and last name
- JWT-based login with automatic token refresh
- Persistent sessions via AsyncStorage (mobile) and Django sessions (web)
- Account deletion with username confirmation

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login and receive JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Get current user details |
| GET | `/api/dashboard/` | Summary of trips, balances, and personal expenses |
| POST | `/api/trips/create/` | Create a new trip |
| GET | `/api/trips/<id>/` | Trip details, expenses, balances, settlements |
| DELETE | `/api/trips/<id>/delete/` | Delete a trip |
| POST | `/api/trips/<id>/add-expense/` | Add an expense to a trip |
| DELETE | `/api/expenses/<id>/delete/` | Delete an expense |
| POST | `/api/trips/<id>/settle/` | Record a settlement between members |
| GET | `/api/personal/` | List personal expenses with totals |
| POST | `/api/personal/add/` | Add a personal expense |
| DELETE | `/api/personal/<id>/delete/` | Delete a personal expense |
| GET | `/api/friends/` | Friends list, pending requests, search |
| POST | `/api/friends/request/<user_id>/` | Send a friend request |
| POST | `/api/friends/accept/<request_id>/` | Accept a friend request |
| DELETE | `/api/friends/decline/<request_id>/` | Decline a friend request |
| DELETE | `/api/friends/remove/<user_id>/` | Remove a friend |
| POST | `/api/account/delete/` | Delete the current user account |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### Backend (Django)

```bash
git clone https://github.com/pushpitshukla28/SplitEase.git
cd SplitEase

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # Fill in SECRET_KEY and other values

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The web app will be available at `http://127.0.0.1:8000`.

### Environment Variables

Create a `.env` file based on `.env.example`:

```
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=                   # Leave empty to use SQLite locally
```

### Mobile App (React Native)

```bash
cd SplitEaseApp

npm install

npx expo start
```

To run on a physical device, scan the QR code with the Expo Go app.
To run on an emulator, press `a` for Android or `i` for iOS in the Expo CLI.

The app points to the live backend at `https://splitease-1vlc.onrender.com` by default. To use a local backend, update the base URL in `src/api/client.js`.

### Android APK

A pre-built APK is available for direct installation on Android devices without needing the Expo Go app. Download it and enable "Install from unknown sources" in your device settings before installing.

---

## Deployment

### Backend on Render

The repository includes a `render.yaml` file for one-click deployment on Render.

Required environment variables on Render:
- `SECRET_KEY` - Django secret key (auto-generated if using the YAML)
- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Set to `False`
- `ALLOWED_HOSTS` - Your Render service domain

The `build.sh` script handles dependency installation, static file collection, and database migrations automatically on each deploy.

**Planned:** Migration from Render to DigitalOcean for improved performance and control.

### Mobile App via EAS

```bash
npm install -g eas-cli
eas login
eas build --platform android --profile preview
```

Build profiles are defined in `eas.json`. The `preview` profile produces an APK for internal distribution; the `production` profile targets app store submission.

---

## Database Models

| Model | Description |
|-------|-------------|
| `Trip` | A group trip with a name, description, and creator |
| `TripMember` | Membership linking a user to a trip |
| `Expense` | An expense within a trip, paid by one member |
| `ExpenseSplit` | The amount each member owes for an expense |
| `Settlement` | A recorded payment between two trip members |
| `FriendRequest` | A friend connection request between two users |
| `PersonalExpense` | A personal (non-trip) expense with a category |

---

## Project Structure

```
SplitEaseCode/
├── core/                   Django app: models, views, API views, URLs
│   ├── models.py           All database models
│   ├── views.py            Web views (HTML responses)
│   ├── api_views.py        REST API views
│   └── urls.py             URL routing
├── splitease/              Django project config
│   ├── settings.py
│   └── urls.py
├── templates/              HTML templates for the web frontend
├── static/                 CSS, JS, and image assets
├── requirements.txt
├── render.yaml             Render deployment config
└── build.sh                Render build script

SplitEaseApp/
├── src/
│   ├── api/client.js       Axios instance with JWT interceptor
│   ├── context/AuthContext.js  Auth state and token management
│   └── screens/            All app screens (Login, Dashboard, Trips, etc.)
├── App.js                  Navigation structure
├── app.json                Expo app config
└── eas.json                EAS build profiles
```

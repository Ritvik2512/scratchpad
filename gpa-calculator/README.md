# 🎓 Student GPA Calculator

A modern, responsive React web application that helps students calculate and track their Grade Point Average (GPA) efficiently. Built with React.js, this application provides real-time calculations, data persistence, and a seamless user experience across all devices.

## 🌟 Features

- ✅ **Real-time GPA Calculation** - Instant weighted GPA computation as you add subjects
- 📊 **8-Grade System Support** - S, A, B, C, D, E, F, N (90-100 to Backlog/Fail)
- 🔄 **CRUD Operations** - Add, view, delete subjects with confirmation dialogs
- 💾 **Data Persistence** - Automatic save/load using localStorage
- 📱 **Fully Responsive** - Optimized for desktop, tablet, and mobile devices
- ✨ **Toast Notifications** - User-friendly feedback for all actions
- ⌨️ **Keyboard Shortcuts** - Press Enter to add subjects quickly
- 🎨 **Modern UI/UX** - Clean interface with smooth animations
- ✔️ **Form Validation** - Real-time input validation and error handling
- 🔢 **Weighted Calculation** - Accurate GPA based on credit hours

## 🛠️ Technologies Used

- React.js
- JavaScript ES6+
- CSS3 (Grid, Flexbox, Custom Properties)
- HTML5 (Semantic)
- React Hooks (useState, useEffect)
- localStorage API

## 📂 Project Structure
```
gpa-calculator-react/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── Hero.jsx
│   │   ├── Calculator.jsx
│   │   ├── SubjectForm.jsx
│   │   ├── SubjectTable.jsx
│   │   ├── GpaResult.jsx
│   │   ├── HowItWorks.jsx
│   │   ├── About.jsx
│   │   ├── Footer.jsx
│   │   └── Notification.jsx
│   ├── App.jsx
│   ├── App.css
│   └── index.js
└── package.json
```

## 🎮 Usage

1. **Add a Subject**
   - Enter subject name
   - Input credit hours (1-6)
   - Select grade achieved
   - Click "Add Subject"

2. **View Subjects**
   - All added subjects appear in the table
   - See subject name, credits, grade, and grade points

3. **Calculate GPA**
   - Click "Calculate GPA" button
   - View total credits and final GPA
   - GPA updates automatically as you add/remove subjects

4. **Delete Subjects**
   - Click the × button next to any subject
   - Confirm deletion in the dialog

5. **Reset**
   - Click "Reset All" to clear all subjects
   - Confirm to start fresh

## 💡 Key Features Explained

### Component Architecture
The application is built with 9+ reusable React components:
- **Header** - Navigation and branding
- **Hero** - Introduction section
- **Calculator** - Main calculator logic container
- **SubjectForm** - Input form for adding subjects
- **SubjectTable** - Display all subjects in a table
- **GpaResult** - Show calculated GPA and total credits
- **Notification** - Toast notifications for user feedback
- **HowItWorks** - Educational section on GPA calculation
- **About** - Project information
- **Footer** - Copyright and credits

### State Management
Uses React Hooks for efficient state management:
- `useState` - Managing subjects array, form inputs, notifications
- `useEffect` - Auto-saving to localStorage, auto-calculating GPA

### Data Persistence
- Subjects are automatically saved to browser's localStorage
- Data persists across browser sessions
- Automatic recovery on page reload

### Responsive Design
- **Desktop**: Multi-column grid layout
- **Tablet**: Adapted responsive layout
- **Mobile**: Single-column stacked layout
- Uses CSS Grid and Flexbox for flexibility

## 🔒 Data Privacy

- All data is stored locally in your browser
- No data is sent to any server
- No user accounts or authentication required
- Clear localStorage to remove all data

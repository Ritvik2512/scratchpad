import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import Hero from './components/Hero';
import Calculator from './components/Calculator';
import HowItWorks from './components/HowItWorks';
import About from './components/About';
import Footer from './components/Footer';
import Notification from './components/Notification';

// Grade Points Mapping
export const gradePoints = {
  'S': 10.0,
  'A': 9.0,
  'B': 8.0,
  'C': 7.0,
  'D': 6.0,
  'E': 5.0,
  'F': 0.0,
  'N': 0.0
};

function App() {
  // State Management
  const [subjects, setSubjects] = useState([]);
  const [notification, setNotification] = useState(null);

  // Load from localStorage on mount
  useEffect(() => {
    const savedSubjects = localStorage.getItem('gpaCalculatorSubjects');
    if (savedSubjects) {
      try {
        setSubjects(JSON.parse(savedSubjects));
      } catch (error) {
        console.error('Error loading saved data:', error);
      }
    }
  }, []);

  // Save to localStorage whenever subjects change
  useEffect(() => {
    localStorage.setItem('gpaCalculatorSubjects', JSON.stringify(subjects));
  }, [subjects]);

  // Add Subject
  const addSubject = (subject) => {
    const newSubject = {
      id: Date.now(),
      ...subject,
      points: gradePoints[subject.grade]
    };
    setSubjects([...subjects, newSubject]);
    showNotification('Subject added successfully!', 'success');
  };

  // Delete Subject
  const deleteSubject = (id) => {
    if (window.confirm('Are you sure you want to delete this subject?')) {
      setSubjects(subjects.filter(subject => subject.id !== id));
      showNotification('Subject deleted successfully!', 'success');
    }
  };

  // Reset Calculator
  const resetCalculator = () => {
    if (subjects.length > 0) {
      if (window.confirm('Are you sure you want to reset? All data will be lost.')) {
        setSubjects([]);
        showNotification('Calculator reset successfully!', 'success');
      }
    } else {
      setSubjects([]);
      showNotification('Calculator reset successfully!', 'success');
    }
  };

  // Show Notification
  const showNotification = (message, type) => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div className="App">
      <Header />
      <main className="main">
        <Hero />
        <Calculator
          subjects={subjects}
          addSubject={addSubject}
          deleteSubject={deleteSubject}
          resetCalculator={resetCalculator}
          showNotification={showNotification}
        />
        <HowItWorks />
        <About />
      </main>
      <Footer />
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
    </div>
  );
}

export default App;
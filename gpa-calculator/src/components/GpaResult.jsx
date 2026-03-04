import React, { useState, useEffect } from 'react';

const GpaResult = ({ subjects, resetCalculator, showNotification }) => {
  const [totalCredits, setTotalCredits] = useState(0);
  const [gpa, setGpa] = useState(0);

  const calculateGPA = () => {
    if (subjects.length === 0) {
      showNotification('Please add at least one subject to calculate GPA', 'error');
      return;
    }

    let credits = 0;
    let totalPoints = 0;

    subjects.forEach(subject => {
      credits += subject.credits;
      totalPoints += (subject.credits * subject.points);
    });

    const calculatedGpa = credits > 0 ? (totalPoints / credits) : 0;

    setTotalCredits(credits);
    setGpa(calculatedGpa);

    showNotification(`GPA Calculated: ${calculatedGpa.toFixed(2)}`, 'success');
  };

  // Auto-calculate when subjects change
  useEffect(() => {
    if (subjects.length > 0) {
      let credits = 0;
      let totalPoints = 0;

      subjects.forEach(subject => {
        credits += subject.credits;
        totalPoints += (subject.credits * subject.points);
      });

      const calculatedGpa = credits > 0 ? (totalPoints / credits) : 0;
      setTotalCredits(credits);
      setGpa(calculatedGpa);
    } else {
      setTotalCredits(0);
      setGpa(0);
    }
  }, [subjects]);

  return (
    <div className="gpa-result">
      <div className="result-card">
        <div className="result-item">
          <span className="result-label">Total Credits:</span>
          <span className="result-value">{totalCredits}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Your GPA:</span>
          <span className="result-value result-gpa">{gpa.toFixed(2)}</span>
        </div>
      </div>
      
      <button type="button" className="btn btn-primary" onClick={calculateGPA}>
        Calculate GPA
      </button>
      
      <button type="button" className="btn btn-outline" onClick={resetCalculator}>
        Reset All
      </button>
    </div>
  );
};

export default GpaResult;
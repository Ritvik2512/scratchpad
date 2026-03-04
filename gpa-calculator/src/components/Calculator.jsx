import React from 'react';
import SubjectForm from './SubjectForm';
import SubjectTable from './SubjectTable';
import GpaResult from './GpaResult';

const Calculator = ({ subjects, addSubject, deleteSubject, resetCalculator, showNotification }) => {
  return (
    <section id="calculator" className="calculator-section">
      <div className="container">
        <h3 className="section-title">Enter Your Courses</h3>
        
        <SubjectForm addSubject={addSubject} showNotification={showNotification} />
        
        <SubjectTable subjects={subjects} deleteSubject={deleteSubject} />
        
        <GpaResult 
          subjects={subjects} 
          resetCalculator={resetCalculator}
          showNotification={showNotification}
        />
      </div>
    </section>
  );
};

export default Calculator;
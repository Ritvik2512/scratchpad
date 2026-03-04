import React from 'react';

const About = () => {
  return (
    <section id="about" className="about-section">
      <div className="container">
        <h3 className="section-title">About This Calculator</h3>
        <div className="about-content">
          <p>
            This Student GPA Calculator is designed to help students easily calculate their 
            Grade Point Average based on their course grades and credit hours. Simply enter 
            your subjects, select the appropriate grades, and let the calculator do the work.
          </p>
          <p>
            <strong>Important Notes:</strong>
          </p>
          <ul className="about-list">
            <li>Grades marked as 'N' (Backlog/Fail) carry 0 grade points and will lower your GPA</li>
            <li>Make sure to enter accurate credit hours for each subject</li>
            <li>Your GPA is calculated on a 10-point scale</li>
            <li>All calculations are performed in real-time in your browser</li>
          </ul>
        </div>
      </div>
    </section>
  );
};

export default About;
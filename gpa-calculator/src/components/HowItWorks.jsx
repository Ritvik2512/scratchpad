import React from 'react';

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="info-section">
      <div className="container">
        <h3 className="section-title">How GPA is Calculated</h3>
        
        <div className="info-grid">
          {/* Grading Scale Card */}
          <div className="info-card">
            <h4 className="info-card-title">Grading Scale</h4>
            <div className="grade-table">
              <div className="grade-row">
                <span className="grade-letter">S</span>
                <span className="grade-range">90-100</span>
                <span className="grade-points">10.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">A</span>
                <span className="grade-range">80-89</span>
                <span className="grade-points">9.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">B</span>
                <span className="grade-range">70-79</span>
                <span className="grade-points">8.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">C</span>
                <span className="grade-range">60-69</span>
                <span className="grade-points">7.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">D</span>
                <span className="grade-range">50-59</span>
                <span className="grade-points">6.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">E</span>
                <span className="grade-range">40-49</span>
                <span className="grade-points">5.0</span>
              </div>
              <div className="grade-row">
                <span className="grade-letter">F</span>
                <span className="grade-range">0-39</span>
                <span className="grade-points">0.0</span>
              </div>
              <div className="grade-row backlog">
                <span className="grade-letter">N</span>
                <span className="grade-range">Backlog/Fail</span>
                <span className="grade-points">0.0</span>
              </div>
            </div>
          </div>

          {/* Calculation Method Card */}
          <div className="info-card">
            <h4 className="info-card-title">Calculation Method</h4>
            <div className="calculation-steps">
              <div className="step">
                <span className="step-number">1</span>
                <div className="step-content">
                  <strong>Multiply Credits by Grade Points</strong>
                  <p>For each subject, multiply the credit hours by the grade points earned.</p>
                </div>
              </div>
              <div className="step">
                <span className="step-number">2</span>
                <div className="step-content">
                  <strong>Sum Total Points</strong>
                  <p>Add up all the grade points × credits for all subjects.</p>
                </div>
              </div>
              <div className="step">
                <span className="step-number">3</span>
                <div className="step-content">
                  <strong>Divide by Total Credits</strong>
                  <p>Divide the total points by the total number of credit hours.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Example Calculation Card */}
          <div className="info-card full-width">
            <h4 className="info-card-title">Example Calculation</h4>
            <div className="example-content">
              <p className="example-intro">Let's calculate GPA for a student with three subjects:</p>
              <div className="example-table">
                <table>
                  <thead>
                    <tr>
                      <th>Subject</th>
                      <th>Credits</th>
                      <th>Grade</th>
                      <th>Points</th>
                      <th>Credits × Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Data Structures</td>
                      <td>3</td>
                      <td>S (10.0)</td>
                      <td>10.0</td>
                      <td>30.0</td>
                    </tr>
                    <tr>
                      <td>Web Development</td>
                      <td>4</td>
                      <td>A (9.0)</td>
                      <td>9.0</td>
                      <td>36.0</td>
                    </tr>
                    <tr>
                      <td>Database Management</td>
                      <td>3</td>
                      <td>B (8.0)</td>
                      <td>8.0</td>
                      <td>24.0</td>
                    </tr>
                    <tr className="total-row">
                      <td><strong>Total</strong></td>
                      <td><strong>10</strong></td>
                      <td>—</td>
                      <td>—</td>
                      <td><strong>90.0</strong></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="formula">
                <p><strong>GPA = Total Points ÷ Total Credits</strong></p>
                <p className="formula-calculation">GPA = 90.0 ÷ 10 = <strong>9.00</strong></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
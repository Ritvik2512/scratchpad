import React, { useState } from 'react';

const SubjectForm = ({ addSubject, showNotification }) => {
  const [formData, setFormData] = useState({
    name: '',
    credits: '',
    grade: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      showNotification('Please enter a subject name', 'error');
      return;
    }
    
    const credits = parseInt(formData.credits);
    if (!credits || credits < 1 || credits > 6) {
      showNotification('Please enter valid credit hours (1-6)', 'error');
      return;
    }
    
    if (!formData.grade) {
      showNotification('Please select a grade', 'error');
      return;
    }

    // Add subject
    addSubject({
      name: formData.name.trim(),
      credits: credits,
      grade: formData.grade
    });

    // Reset form
    setFormData({
      name: '',
      credits: '',
      grade: ''
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="input-form">
      <div className="form-group">
        <label htmlFor="name">Subject Name</label>
        <input
          type="text"
          id="name"
          name="name"
          placeholder="e.g., Data Structures"
          className="form-input"
          value={formData.name}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
        />
      </div>

      <div className="form-group">
        <label htmlFor="credits">Credit Hours</label>
        <input
          type="number"
          id="credits"
          name="credits"
          placeholder="e.g., 3"
          min="1"
          max="6"
          className="form-input"
          value={formData.credits}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
        />
      </div>

      <div className="form-group">
        <label htmlFor="grade">Grade</label>
        <select
          id="grade"
          name="grade"
          className="form-input"
          value={formData.grade}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
        >
          <option value="">Select Grade</option>
          <option value="S">S (90-100)</option>
          <option value="A">A (80-89)</option>
          <option value="B">B (70-79)</option>
          <option value="C">C (60-69)</option>
          <option value="D">D (50-59)</option>
          <option value="E">E (40-49)</option>
          <option value="F">F (0-39)</option>
          <option value="N">N (Backlog/Fail)</option>
        </select>
      </div>

      <button type="button" className="btn btn-secondary" onClick={handleSubmit}>
        Add Subject
      </button>
    </div>
  );
};

export default SubjectForm;
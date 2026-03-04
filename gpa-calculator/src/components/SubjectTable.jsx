import React from 'react';

const SubjectTable = ({ subjects, deleteSubject }) => {
  return (
    <div className="subjects-container">
      <h4 className="subjects-heading">Your Subjects</h4>
      
      <div className="table-responsive">
        <table className="subjects-table">
          <thead>
            <tr>
              <th>Subject Name</th>
              <th>Credit Hours</th>
              <th>Grade</th>
              <th>Grade Points</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {subjects.length === 0 ? (
              <tr className="empty-state">
                <td colSpan="5" className="empty-message">
                  No subjects added yet. Add your first subject above!
                </td>
              </tr>
            ) : (
              subjects.map((subject) => (
                <tr key={subject.id} className="subject-row">
                  <td>{subject.name}</td>
                  <td>{subject.credits}</td>
                  <td>{subject.grade}</td>
                  <td>{subject.points.toFixed(1)}</td>
                  <td>
                    <button
                      className="btn-delete"
                      onClick={() => deleteSubject(subject.id)}
                      title="Delete"
                    >
                      ×
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SubjectTable;
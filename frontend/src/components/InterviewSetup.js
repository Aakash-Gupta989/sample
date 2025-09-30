import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  ArrowRight,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import './InterviewSetup.css';

const InterviewSetup = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    company: '',
    position: '',
    resume: null,
    jobDescription: '',
    interviewerLinkedIn: '',
    interviewType: '',
  });

  const [errors, setErrors] = useState({});
  const [resumeFileName, setResumeFileName] = useState('');

  const interviewTypes = [
    { value: 'behavioral', label: 'Behavioral' },
    { value: 'technical', label: 'Technical' },
    { value: 'behavioral-technical', label: 'Behavioral + Technical' },
    { value: 'coding', label: 'Coding Interview' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        setFormData(prev => ({
          ...prev,
          resume: file
        }));
        setResumeFileName(file.name);
        setErrors(prev => ({
          ...prev,
          resume: ''
        }));
      } else {
        setErrors(prev => ({
          ...prev,
          resume: 'Please upload a PDF file'
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    
    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required';
    }
    
    if (!formData.position.trim()) {
      newErrors.position = 'Position is required';
    }
    
    if (!formData.jobDescription.trim()) {
      newErrors.jobDescription = 'Job description is required';
    }
    
    if (!formData.interviewType) {
      newErrors.interviewType = 'Please select an interview type';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      // Navigate to loading page with form data
      navigate('/loading', { state: { formData } });
    }
  };

  const isFormValid = formData.firstName && formData.lastName && formData.company && 
                     formData.position && formData.jobDescription && formData.interviewType;

  return (
    <div className="setup-container">
      <div className="setup-content">
        <div className="setup-header">
          <h1>Interview Setup</h1>
        </div>

        <form onSubmit={handleSubmit} className="setup-form">
          {/* Personal Information */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="firstName">First Name *</label>
              <input
                id="firstName"
                type="text"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                placeholder="First name"
                className={errors.firstName ? 'error' : ''}
              />
              {errors.firstName && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  {errors.firstName}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="lastName">Last Name *</label>
              <input
                id="lastName"
                type="text"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                placeholder="Last name"
                className={errors.lastName ? 'error' : ''}
              />
              {errors.lastName && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  {errors.lastName}
                </div>
              )}
            </div>
          </div>

          {/* Company & Position */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="company">Company *</label>
              <input
                id="company"
                type="text"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                placeholder="Company name"
                className={errors.company ? 'error' : ''}
              />
              {errors.company && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  {errors.company}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="position">Position *</label>
              <input
                id="position"
                type="text"
                value={formData.position}
                onChange={(e) => handleInputChange('position', e.target.value)}
                placeholder="Position title"
                className={errors.position ? 'error' : ''}
              />
              {errors.position && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  {errors.position}
                </div>
              )}
            </div>
          </div>

          {/* Resume Upload */}
          <div className="form-group">
            <label htmlFor="resume">Resume (Optional)</label>
            <div className="file-upload">
              <input
                id="resume"
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="file-input"
              />
              <label htmlFor="resume" className="file-upload-label">
                <Upload size={18} />
                {resumeFileName ? resumeFileName : 'Choose PDF file'}
              </label>
              {resumeFileName && (
                <div className="file-success">
                  <CheckCircle size={14} />
                  Uploaded
                </div>
              )}
              {errors.resume && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  {errors.resume}
                </div>
              )}
            </div>
          </div>

          {/* Job Description */}
          <div className="form-group">
            <label htmlFor="jobDescription">Job Description *</label>
            <textarea
              id="jobDescription"
              name="jobDescription"
              value={formData.jobDescription}
              onChange={(e) => handleInputChange('jobDescription', e.target.value)}
              placeholder="Paste job description here..."
              rows={4}
              className={errors.jobDescription ? 'error' : ''}
            />
            {errors.jobDescription && (
              <div className="error-message">
                <AlertCircle size={14} />
                {errors.jobDescription}
              </div>
            )}
          </div>

          {/* Interviewer LinkedIn Profile */}
          <div className="form-group">
            <label htmlFor="interviewerLinkedIn">Interviewer's LinkedIn Profile (Optional)</label>
            <textarea
              id="interviewerLinkedIn"
              name="interviewerLinkedIn"
              value={formData.interviewerLinkedIn}
              onChange={(e) => handleInputChange('interviewerLinkedIn', e.target.value)}
              placeholder="Paste interviewer's complete LinkedIn profile content here..."
              rows={4}
            />
          </div>

          {/* Interview Type */}
          <div className="form-group">
            <label htmlFor="interviewType">Interview Type *</label>
            <select
              id="interviewType"
              value={formData.interviewType}
              onChange={(e) => handleInputChange('interviewType', e.target.value)}
              className={errors.interviewType ? 'error' : ''}
            >
              <option value="">Select interview type</option>
              {interviewTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            {errors.interviewType && (
              <div className="error-message">
                <AlertCircle size={14} />
                {errors.interviewType}
              </div>
            )}
          </div>


          {/* Submit Button */}
          <button
            type="submit"
            className={`submit-btn ${isFormValid ? 'ready' : 'disabled'}`}
            disabled={!isFormValid}
          >
            Start Interview
            <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default InterviewSetup;

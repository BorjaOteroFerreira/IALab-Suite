import React from 'react';
import PropTypes from 'prop-types';
import { Star, ChevronUp, ChevronDown, AlertCircle } from 'lucide-react';

const ReadmeSection = React.memo(({
  open,
  onToggle,
  readmeHtml,
  loading,
  error,
  strings
}) => (
  <section className="readme-section" style={{background: 'rgba(135,206,235,0.04)', borderRadius: 12, boxShadow: '0 2px 8px #0001', padding: '18px 16px', marginBottom: 0, transition: 'all 0.25s'}}>
    <div className="sidebar-header" style={{ marginTop: 16, cursor:'pointer' }} onClick={onToggle}>
      <h5 style={{background: 'linear-gradient(90deg, #87CEEB, #b983ff, #87CEEB)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', color: 'transparent', fontWeight: 800}}>
        <Star size={18}/> {strings.viewReadme}
      </h5>
      {open ? <ChevronUp/> : <ChevronDown/>}
    </div>
    {open && (
      <div className="readme-content">
        {loading ? (
          <div className="loading"><div className="spinner"/>{strings.loadingReadme}</div>
        ) : error ? (
          <div className="error"><AlertCircle size={16}/> {strings.readmeError}</div>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: readmeHtml }} />
        )}
      </div>
    )}
  </section>
));

ReadmeSection.propTypes = {
  open: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
  readmeHtml: PropTypes.string,
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object
  ]),
  strings: PropTypes.object.isRequired
};

export default ReadmeSection;

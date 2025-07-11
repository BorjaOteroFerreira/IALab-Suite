import React from 'react';
import PropTypes from 'prop-types';
import { Download, ChevronUp, ChevronDown, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const DownloadSection = React.memo(({
  open,
  onToggle,
  files,
  loadingFiles,
  downloadStatus,
  handleDownload,
  strings,
  hasVision
}) => (
  <section className="download-section" style={{background: 'rgba(135,206,235,0.06)', borderRadius: 0, boxShadow: '0 2px 8px #0001', padding: '18px', marginBottom: 18, transition: 'all 0.25s'}}>
    <div className="sidebar-header" onClick={onToggle} style={{cursor:'pointer'}}>
      <h5 style={{background: 'linear-gradient(90deg, #87CEEB, #b983ff, #87CEEB)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', color: 'transparent', fontWeight: 800, padding: '18px 18px 12px 18px'}}>
        <Download size={18}/> {strings.downloadOptions}
        {hasVision && <span className="model-meta-vision" style={{ marginLeft: '8px' }}>{strings.vision}</span>}
      </h5>
      {open ? <ChevronUp/> : <ChevronDown/>}
    </div>
    {open && (
      <div className="section-scrollable" style={{transition:'all 0.25s'}}>
        {loadingFiles && (
          <div className="loading"><div className="spinner"/>{strings.loadingFiles}</div>
        )}
        {files?.map((file, idx) => {
          const key = `${file.downloadUrl}-${file.name}`;
          const status = downloadStatus[key];
          const fileQuant = (file.name.match(/Q(\d+)((_[A-Z])+)?/i) || [null])[0]?.toUpperCase();
          const fileType = (file.name.match(/(chat|instruct|base|code)/i) || [null])[0]?.toLowerCase();
          const isVision = file.name.toLowerCase().endsWith('.mmproj');
          return (
            <div key={idx} className="model-card download-item">
              <div className="model-card-info download-info">
                <div className="model-card-name download-name">{file.name}</div>
                <div className="model-card-meta">
                  <span className="model-meta-size download-size">{file.size}</span>
                  {fileQuant && <span className="model-meta-quantization">{fileQuant}</span>}
                  {fileType && <span className="model-meta-type">{fileType}</span>}
                  {isVision && <span className="model-meta-vision">{strings.vision}</span>}
                </div>
              </div>
              <button
                className={`download-button btn btn-primary ${status||''}`}
                onClick={() => handleDownload(file.downloadUrl, file.name)}
                disabled={status==='downloading'}
              >
                {status==='downloading' && <Clock size={14}/>}
                {status==='completed'   && <CheckCircle size={14}/>}
                {!status && <Download size={14}/>}
                {status==='downloading' ? strings.downloading :
                 status==='completed'   ? strings.completed :
                 strings.download}
              </button>
            </div>
          );
        })}
        {!loadingFiles && files?.length===0 && (
          <div className="empty-state">
            <AlertCircle size={24}/>
            <p>{strings.noFiles}</p>
          </div>
        )}
      </div>
    )}
  </section>
));

DownloadSection.propTypes = {
  open: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    size: PropTypes.string,
    downloadUrl: PropTypes.string.isRequired
  })),
  loadingFiles: PropTypes.bool,
  downloadStatus: PropTypes.object,
  handleDownload: PropTypes.func.isRequired,
  strings: PropTypes.object.isRequired,
  hasVision: PropTypes.bool
};

export default DownloadSection;

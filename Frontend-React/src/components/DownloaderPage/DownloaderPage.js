import React, { useState, useEffect } from 'react';
import {
  Search,
  Download,
  Star,
  AlertCircle,
  CheckCircle,
  Clock,
  HardDrive,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  X
} from 'lucide-react';

import './DownloaderPage.css';

const FunctionalLMStudioDownloader = ({ open, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadStatus, setDownloadStatus] = useState({});
  const [sortBy, setSortBy] = useState('lastModified');
  const [error, setError] = useState(null);
  const [downloadsOpen, setDownloadsOpen] = useState(true);
  const [showReadme, setShowReadme] = useState(false);
  const [readmeHtml, setReadmeHtml] = useState('');
  const [readmeLoading, setReadmeLoading] = useState(false);
  const [readmeError, setReadmeError] = useState(null);

  const searchModels = async (query = 'GGUF', limit = 30) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `https://huggingface.co/api/models?search=${encodeURIComponent(query)}&filter=gguf&sort=${sortBy}&limit=${limit}`
      );
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      setModels(data.filter(m =>
        m.tags?.includes('gguf') ||
        m.id.toLowerCase().includes('gguf')
      ));
    } catch (err) {
      setError(`Error al buscar modelos: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Extrae badges: tamaño, tipo, cuantización y visión
  const getModelBadges = (model) => {
    // Tamaño por tag
    const sizeTag = model.tags?.find(t => /^\d+\.?\d*[Bb]$/i.test(t));
    // Cuantización por tag
    const quantTag = model.tags?.find(t => /Q(\d+)((_[A-Z])+)?/i.test(t))?.toUpperCase();
    // Tipo por pipeline_tag
    const typeTag = model.pipeline_tag;

    // Si el modelo ya tiene archivos cargados (selectedModel.files), usar el archivo principal .gguf
    let fileType = null, fileQuant = null, hasVision = false;
    if (model.files && Array.isArray(model.files) && model.files.length > 0) {
      const mainFile = model.files.find(f => f.name.endsWith('.gguf')) || model.files[0];
      if (mainFile) {
        // Tipo por nombre de archivo
        fileType = (mainFile.name.match(/(chat|instruct|base|code)/i) || [null])[0]?.toLowerCase();
        // Cuantización por nombre de archivo (detecta Q4_K, Q4_M, Q4_KM, Q4_K_S, Q4_K_M, etc)
        fileQuant = (mainFile.name.match(/Q(\d+)((_[A-Z])+)?/i) || [null])[0]?.toUpperCase();
      }
      hasVision = model.files.some(f => f.name.toLowerCase().includes('mmproj'));
    }

    return {
      size: sizeTag,
      quant: fileQuant || quantTag,
      type: fileType || typeTag,
      vision: hasVision
    };
  };

  const getModelFiles = async (modelId) => {
    try {
      const res = await fetch(`https://huggingface.co/api/models/${modelId}/tree/main`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      const files = await res.json();
      return files
        .filter(f =>
          (f.path.endsWith('.gguf') || f.path.toLowerCase().includes('mmproj'))
          && f.type === 'file'
        )
        .map(f => ({
          name: f.path,
          size: formatFileSize(f.size || 0),
          downloadUrl: `https://huggingface.co/${modelId}/resolve/main/${f.path}`
        }));
    } catch {
      return [];
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024, sizes = ['B','KB','MB','GB','TB'];
    const i = Math.floor(Math.log(bytes)/Math.log(k));
    return `${(bytes/Math.pow(k,i)).toFixed(2)} ${sizes[i]}`;
  };

  const selectModel = async (model) => {
    setSelectedModel({ ...model, files: [], loadingFiles: true });
    const files = await getModelFiles(model.id);
    setSelectedModel(prev => ({ ...prev, files, loadingFiles: false }));
    setDownloadsOpen(true);
  };

  useEffect(() => { searchModels(); }, [sortBy]);

  const handleDownload = (url, name) => {
    const key = `${url}-${name}`;
    setDownloadStatus(prev => ({ ...prev, [key]: 'downloading' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => {
      setDownloadStatus(prev => ({ ...prev, [key]: 'completed' }));
    }, 2000);
  };

  const formatTimeAgo = (dateStr) => {
    const d = new Date(dateStr), now = new Date();
    const days = Math.ceil(Math.abs(now - d)/(1000*60*60*24));
    if (days === 1) return '1 day ago';
    if (days < 30) return `${days} days ago`;
    if (days < 365) return `${Math.floor(days/30)} months ago`;
    return `${Math.floor(days/365)} years ago`;
  };

  const hasVision = selectedModel?.files?.some(f =>
    f.name.toLowerCase().endsWith('.mmproj')
  );

  // Carga asíncrona del README
  const fetchReadme = async (modelId) => {
    setReadmeLoading(true);
    setReadmeError(null);
    setReadmeHtml('');
    try {
      const res = await fetch(`https://huggingface.co/${modelId}/raw/main/README.md`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      const text = await res.text();
      setReadmeHtml(text);
    } catch (err) {
      setReadmeError(`Error al cargar README: ${err.message}`);
    } finally {
      setReadmeLoading(false);
    }
  };

  // Cargar README cuando se selecciona un modelo y se despliega el apartado
  useEffect(() => {
    if (showReadme && selectedModel) {
      setReadmeLoading(true);
      setReadmeError(null);
      setReadmeHtml('');
      fetch(`https://huggingface.co/${selectedModel.id}/raw/main/README.md`)
        .then(res => {
          if (!res.ok) throw new Error('No se pudo cargar el README');
          return res.text();
        })
        .then(md => {
          // Convertir markdown a HTML usando showdown (si está disponible)
          if (window.showdown) {
            const converter = new window.showdown.Converter({tables:true,simpleLineBreaks:true,emoji:true,openLinksInNewWindow:true});
            setReadmeHtml(converter.makeHtml(md));
          } else {
            // Si showdown no está disponible, cargarlo dinámicamente y luego convertir
            import('showdown').then(module => {
              const showdown = module.default || module;
              const converter = new showdown.Converter({tables:true,simpleLineBreaks:true,emoji:true,openLinksInNewWindow:true});
              setReadmeHtml(converter.makeHtml(md));
            }).catch(() => {
              setReadmeHtml('<pre class="readme-pre">'+md+'</pre>');
            });
          }
        })
        .catch(err => setReadmeError('No se pudo cargar el README'))
        .finally(() => setReadmeLoading(false));
    }
  }, [showReadme, selectedModel]);

  return (
    open ? (
      <div className="gguf-modal-overlay">
        <div className="gguf-modal">
          <button className="gguf-modal-close" onClick={onClose} title="Cerrar" style={{ position: 'absolute', top: 10, right: 10, padding: 0, width: 32, height: 32, minWidth: 0, minHeight: 0, background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', borderRadius: '50%', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
            <X size={18} />
          </button>
          <div className="lm-studio-app">
            <div className="sidebar">
              <div className="search-header">
                <div className="search-form">
                  <Search size={16} className="search-icon"/>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Buscar modelos..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    onKeyPress={e => e.key==='Enter'&& searchModels(searchQuery)}
                  />
                </div>
                <div className="filters">
                  <span className="gguf-badge">GGUF</span>
                  <select
                    className="filter-select"
                    value={sortBy}
                    onChange={e => setSortBy(e.target.value)}
                  >
                    <option value="lastModified">Mejor Coincidencia</option>
                    <option value="downloads">Más Descargados</option>
                    <option value="likes">Más Populares</option>
                    <option value="createdAt">Más Recientes</option>
                  </select>
                  <span className="staff-picks">Staff Pick ⭐</span>
                </div>
              </div>

              <div className="models-list">
                {loading && <div className="loading"><div className="spinner"/></div>}
                {error && <div className="error"><AlertCircle size={16}/> {error}</div>}
                {!loading && !error && models.map(model => {
                  const { size, quant, type } = getModelBadges(model);
                  const isSelected = selectedModel?.id === model.id;
                  const tags = model.tags || [];
                  const hasVision = tags.some(t => t.toLowerCase().includes('vision') || t.toLowerCase().includes('mmproj'));
                  const hasTools = tags.some(t => t.toLowerCase().includes('tools'));
                  const hasReasoning = tags.some(t => t.toLowerCase().includes('reasoning'));
                  return (
                    <div
                      key={model.id}
                      className={`model-card ${isSelected?'selected':''}`}
                      onClick={() => selectModel(model)}
                    >
                      <div className="model-card-icon">🤖</div>
                      <div className="model-card-info">
                        <div className="model-card-name" style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                          {model.id.split('/')[1]||model.id}
                          {/* Badges de capabilities en la lista */}
                          {hasVision && (
                            <span className="model-meta-vision" style={{ background: '#f59e42', color: '#fff', borderRadius: 5, padding: '1px 7px', fontSize: 11, fontWeight: 500 }}>visión</span>
                          )}
                          {hasTools && (
                            <span className="model-meta-tools" style={{ background: '#22c55e', color: '#fff', borderRadius: 5, padding: '1px 7px', fontSize: 11, fontWeight: 500 }}>tools</span>
                          )}
                          {hasReasoning && (
                            <span className="model-meta-reasoning" style={{ background: '#a855f7', color: '#fff', borderRadius: 5, padding: '1px 7px', fontSize: 11, fontWeight: 500 }}>reasoning</span>
                          )}
                        </div>
                        <div className="model-card-meta">
                          {size && <span className="model-meta-size">{size}</span>}
                          {quant && <span className="model-meta-quantization">{quant}</span>}
                          {type && <span className="model-meta-type">{type}</span>}
                        </div>
                      </div>
                      {isSelected && <div className="selected-indicator">✓</div>}
                    </div>
                  );
                })}
                {!loading && !error && models.length===0 && (
                  <div className="empty-state">
                    <Search size={48}/>
                    <p>No se encontraron modelos</p>
                  </div>
                )}
              </div>
            </div>

            <div className="main-content">
              {!selectedModel ? (
                <div className="empty-state">
                  <HardDrive size={48}/>
                  <h2>Selecciona un modelo</h2>
                </div>
              ) : (
                <div className="model-details">
                  <h1 className="model-title">
                    {selectedModel.id.split('/')[1]||selectedModel.id}
                    <a
                      href={`https://huggingface.co/${selectedModel.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="model-title-link"
                      title="Ver en HuggingFace"
                    >
                      <ExternalLink size={22} className="model-title-link-icon" />
                    </a>
                  </h1>
                  <p className="model-subtitle">
                    {selectedModel.id} por {selectedModel.id.split('/')[0]}
                  </p>
                  {/* Arquitectura y tamaño en parámetros justo encima de la sección de descargas */}
                  <div className="model-params-row">
                    {selectedModel.cardData?.architecture && (
                      <span className="model-meta-architecture">
                        {selectedModel.cardData.architecture}
                      </span>
                    )}
                    {selectedModel.cardData?.parameters && (
                      <span className="model-meta-params">
                        {selectedModel.cardData.parameters} parámetros
                      </span>
                    )}
                  </div>
                  {/* Badges de capabilities debajo del subtítulo */}
                  <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    {(selectedModel.cardData?.capabilities?.includes('vision') || getModelBadges(selectedModel).vision) && (
                      <span className="model-meta-vision" style={{ background: '#f59e42', color: '#fff', borderRadius: 6, padding: '2px 10px', fontSize: 13, fontWeight: 500 }}>
                        visión
                      </span>
                    )}
                    {(selectedModel.cardData?.capabilities?.includes('tools') || selectedModel.tags?.some(t => t.toLowerCase().includes('tools'))) && (
                      <span className="model-meta-tools" style={{ background: '#22c55e', color: '#fff', borderRadius: 6, padding: '2px 10px', fontSize: 13, fontWeight: 500 }}>
                        tools
                      </span>
                    )}
                    {(selectedModel.cardData?.capabilities?.includes('reasoning') || selectedModel.tags?.some(t => t.toLowerCase().includes('reasoning'))) && (
                      <span className="model-meta-reasoning" style={{ background: '#a855f7', color: '#fff', borderRadius: 6, padding: '2px 10px', fontSize: 13, fontWeight: 500 }}>
                        reasoning
                      </span>
                    )}
                  </div>

                  <div className="download-section">
                    <div
                      className="sidebar-header"
                      style={{ cursor: 'pointer' }}
                      onClick={() => setDownloadsOpen(o => !o)}
                    >
                      <h5>
                        <Download size={18}/> Opciones de Descarga
                        {hasVision && <span className="model-meta-vision" style={{ marginLeft: '8px' }}>visión</span>}
                      </h5>
                      {downloadsOpen ? <ChevronUp/> : <ChevronDown/>}
                    </div>
                    {downloadsOpen && (
                      <div className="section-scrollable" style={{ maxHeight: '372px', overflowY: 'auto' }}>
                        {selectedModel.loadingFiles && (
                          <div className="loading">
                            <div className="spinner"/><span>Cargando archivos...</span>
                          </div>
                        )}
                        {selectedModel.files?.map((file, idx) => {
                          const key = `${file.downloadUrl}-${file.name}`;
                          const status = downloadStatus[key];
                          const fileQuant = (file.name.match(/Q(\d+)((_[A-Z])+)?/i) || [null])[0]?.toUpperCase();
                          const fileType = (file.name.match(/(chat|instruct|base|code)/i) || [null])[0]?.toLowerCase();
                          const isVision = file.name.toLowerCase().endsWith('.mmproj');
                          return (
                            <div key={idx} className="model-card">
                              <div className="model-card-info">
                                <div className="model-card-name">{file.name}</div>
                                <div className="model-card-meta">
                                  <span className="model-meta-size">{file.size}</span>
                                  {fileQuant && <span className="model-meta-quantization">{fileQuant}</span>}
                                  {fileType && <span className="model-meta-type">{fileType}</span>}
                                  {isVision && <span className="model-meta-vision">visión</span>}
                                </div>
                              </div>
                              <button
                                className={`btn btn-primary ${status||''}`}
                                onClick={() => handleDownload(file.downloadUrl, file.name)}
                                disabled={status==='downloading'}
                              >
                                {status==='downloading' && <Clock size={14}/>}
                                {status==='completed'   && <CheckCircle size={14}/>}
                                {!status && <Download size={14}/>}
                                {status==='downloading' ? 'Descargando...' :
                                 status==='completed'   ? 'Completado' :
                                 'Descargar'}
                              </button>
                            </div>
                          );
                        })}
                        {!selectedModel.loadingFiles && selectedModel.files?.length===0 && (
                          <div className="empty-state">
                            <AlertCircle size={24}/>
                            <p>No hay archivos GGUF o MMProj</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Apartado desplegable para el README */}
                  <div className="readme-section">
                    <div
                      className="sidebar-header"
                      style={{ cursor: 'pointer', marginTop: 16 }}
                      onClick={() => setShowReadme(o => !o)}
                    >
                      <h5>
                        <Star size={18}/> Ver README del modelo
                      </h5>
                      {showReadme ? <ChevronUp/> : <ChevronDown/>}
                    </div>
                    {showReadme && (
                      <div className="readme-content" style={{ flex: 1, height: '100%', overflowY: 'auto',  borderRadius: 8, padding: 0, marginTop: 8 }}>
                        {readmeLoading ? (
                          <div className="loading"><div className="spinner"/>Cargando README...</div>
                        ) : readmeError ? (
                          <div className="error"><AlertCircle size={16}/> {readmeError}</div>
                        ) : (
                          <div dangerouslySetInnerHTML={{ __html: readmeHtml }} />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    ) : null
  );
};

export default FunctionalLMStudioDownloader;

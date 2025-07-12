import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  HardDrive,
  ExternalLink,
  Download,
  Star,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useLanguage } from '../../../context/LanguageContext';
import ModelCard from './ModelCard';
import DownloadSection from './DownloadSection';
import ReadmeSection from './ReadmeSection';
import SortSelect from './SortSelect';
import './DownloaderPage.css';

const FunctionalLMStudioDownloader = ({ open, onClose }) => {
  const { getStrings } = useLanguage();
  const strings = getStrings('downloader');
  const general = getStrings('general');

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
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const listRef = useRef();

  const searchModels = async (query = 'GGUF', limit = 30) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `https://huggingface.co/api/models?search=${encodeURIComponent(query)}&filter=gguf&sort=${sortBy}&limit=${limit}`
      );
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      const filtered = data.filter(m =>
        m.tags?.includes('gguf') ||
        m.id.toLowerCase().includes('gguf')
      );
      // Precargar README preview para cada modelo
      const previews = await Promise.all(
        filtered.map(async (model) => {
          try {
            const res = await fetch(`https://huggingface.co/${model.id}/raw/main/README.md`);
            if (res.status === 404) {
              return { ...model, readmePreview: '__NO_README__' };
            }
            if (!res.ok) return { ...model, readmePreview: '__ERROR__' };
            const text = await res.text();
            return { ...model, readmePreview: text.split('\n').slice(0, 2).join(' ') };
          } catch {
            return { ...model, readmePreview: '__ERROR__' };
          }
        })
      );
      setModels(previews);
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
    setDownloadsOpen(false); // Al seleccionar, descargas cerrado
    setShowReadme(true);     // y README abierto
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

  // Vista previa del README (primeras 2 líneas)
  const getReadmePreview = async (modelId) => {
    try {
      const res = await fetch(`https://huggingface.co/${modelId}/raw/main/README.md`);
      if (!res.ok) return '';
      const text = await res.text();
      return text.split('\n').slice(0, 2).join(' ');
    } catch {
      return '';
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

  // Accesibilidad: navegación con teclado
  const handleListKeyDown = (e) => {
    if (!models.length) return;
    if (e.key === 'ArrowDown') {
      setFocusedIndex(i => Math.min(i + 1, models.length - 1));
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setFocusedIndex(i => Math.max(i - 1, 0));
      e.preventDefault();
    } else if (e.key === 'Enter' && focusedIndex >= 0) {
      selectModel(models[focusedIndex]);
      e.preventDefault();
    }
  };

  return (
    open ? (
      <div className="gguf-modal-overlay">
        <div className="gguf-modal">
          <button className="gguf-modal-close" onClick={onClose} title={general.cancel}>
            X
          </button>
          <div className="lm-studio-app">
            <aside className="sidebar">
              <header className="search-header">
                <form className="search-form" onSubmit={e => { e.preventDefault(); searchModels(searchQuery); }}>
                  <Search size={16} className="search-icon"/>
                  <input
                    type="text"
                    className="search-input"
                    placeholder={strings.searchPlaceholder}
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                  />
                </form>
                <div className="filters">
                  <span className="gguf-badge">GGUF</span>
                  <SortSelect
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    strings={strings}
                  />
                </div>
              </header>
              <section
                className="models-list"
                style={{overflowX: 'hidden', padding: 0}}
                tabIndex={0}
                ref={listRef}
                onKeyDown={handleListKeyDown}
                role="listbox"
                aria-activedescendant={focusedIndex >= 0 ? `model-card-${focusedIndex}` : undefined}
              >
                {loading && <div className="loading"><div className="spinner"/>{strings.loadingModels}</div>}
                {error && <div className="error"><span>⚠️</span> {error}</div>}
                {!loading && !error && models.map((model, idx) => (
                  <ModelCard
                    key={model.id}
                    id={`model-card-${idx}`}
                    model={model}
                    isSelected={selectedModel?.id === model.id}
                    isFocused={focusedIndex === idx}
                    tabIndex={0}
                    onClick={() => selectModel(model)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') selectModel(model);
                    }}
                    readmePreview={
                      model.readmePreview === '__ERROR__'
                        ? <span style={{ color: '#b0b0b0', fontStyle: 'italic' }}>{strings.readmeError || 'No se pudo obtener la vista previa del README'}</span>
                        : model.readmePreview === '__NO_README__'
                          ? <span style={{ color: '#b0b0b0', fontStyle: 'italic' }}>{strings.noReadmePreview || 'Este repositorio no tiene README'}</span>
                          : (model.readmePreview && model.readmePreview.trim() !== ''
                            ? model.readmePreview
                            : strings.noReadmePreview || 'Sin descripción disponible')
                    }
                    badges={{
                      ...getModelBadges(model),
                      updatedAt: model.lastModified ? formatTimeAgo(model.lastModified) : null,
                      downloads: model.downloads
                    }}
                    strings={strings}
                  />
                ))}
                {!loading && !error && models.length===0 && (
                  <div className="empty-state">
                    <Search size={48}/>
                    <p>{strings.noModelsFound}</p>
                  </div>
                )}
              </section>
            </aside>
            <main className="main-content" style={{background: 'var(--surface)', borderRadius: '0 1.2rem 1.2rem 0', boxShadow: '0 2px 24px #0002', padding: 0, display: 'flex', flexDirection: 'column'}}>
              {!selectedModel ? (
                <div className="empty-state">
                  <HardDrive size={48}/>
                  <h2>{strings.selectModel}</h2>
                </div>
              ) : (
                <section className="model-details" style={{background: 'rgba(60,60,90,0.10)', borderRadius: 18, margin: 18, boxShadow: '0 2px 16px #0001', padding: '32px 28px 24px 28px', display: 'flex', flexDirection: 'column', gap: 0}}>
                  <h1 className="model-title" style={{fontSize: 28, fontWeight: 800, color: 'var(--accent-primary)', marginBottom: 6, letterSpacing: '-0.5px'}}>
                    {selectedModel.id.split('/')[1]||selectedModel.id}
                    <a
                      href={`https://huggingface.co/${selectedModel.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="model-title-link"
                      title="HuggingFace"
                    >
                      <ExternalLink size={22} className="model-title-link-icon" />
                    </a>
                  </h1>
                  <div style={{background: 'rgba(135,206,235,0.08)', border: '1.5px solid var(--border-light)', borderRadius: 8, padding: '7px 16px', marginBottom: 18, color: '#b983ff', fontSize: 14, fontWeight: 600, display: 'inline-block', maxWidth: 420}}>
                    {selectedModel.id} {strings.by} {selectedModel.id.split('/')[0]}
                  </div>
                  <div className="model-params-row" style={{marginBottom: 18, gap: 12}}>
                    {selectedModel.cardData?.architecture && (
                      <span className="model-meta-architecture" style={{background: '#6366f1', color: '#fff', borderRadius: 7, padding: '4px 14px', fontSize: 14, fontWeight: 600, letterSpacing: '0.5px'}}>
                        {selectedModel.cardData.architecture}
                      </span>
                    )}
                    {selectedModel.cardData?.parameters && (
                      <span className="model-meta-params" style={{background: '#0ea5e9', color: '#fff', borderRadius: 7, padding: '4px 14px', fontSize: 14, fontWeight: 600, letterSpacing: '0.5px'}}>
                        {selectedModel.cardData.parameters} {strings.parameters}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 10, marginBottom: 18, alignItems: 'center', flexWrap: 'wrap' }}>
                    {(selectedModel.cardData?.capabilities?.includes('vision') || getModelBadges(selectedModel).vision) && (
                      <span className="model-meta-vision" style={{ background: '#f59e42', color: '#fff', borderRadius: 8, padding: '4px 16px', fontSize: 15, fontWeight: 700, letterSpacing: '0.5px' }}>
                        {strings.vision}
                      </span>
                    )}
                    {(selectedModel.cardData?.capabilities?.includes('tools') || selectedModel.tags?.some(t => t.toLowerCase().includes('tools'))) && (
                      <span className="model-meta-tools" style={{ background: '#22c55e', color: '#fff', borderRadius: 8, padding: '4px 16px', fontSize: 15, fontWeight: 700, letterSpacing: '0.5px' }}>
                        {strings.tools}
                      </span>
                    )}
                    {(selectedModel.cardData?.capabilities?.includes('reasoning') || selectedModel.tags?.some(t => t.toLowerCase().includes('reasoning'))) && (
                      <span className="model-meta-reasoning" style={{ background: '#a855f7', color: '#fff', borderRadius: 8, padding: '4px 16px', fontSize: 15, fontWeight: 700, letterSpacing: '0.5px' }}>
                        {strings.reasoning}
                      </span>
                    )}
                  </div>
                  {/* Sección de descargas con cabecera desplegable e icono, colapsable visualmente */}
                  <div className={`download-section collapsible-section${downloadsOpen ? ' open' : ''}`} style={{borderRadius: 12, boxShadow: downloadsOpen ? '0 2px 12px #0001' : 'none', background: downloadsOpen ? 'rgba(135,206,235,0.07)' : 'transparent', marginBottom: 18, overflow: 'hidden', transition: 'all 0.25s'}}> 
                    <button
                      className="section-toggle-title"
                      style={{margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: '18px 0 18px 0', outline: 'none', display: 'flex', alignItems: 'center', gap: 8, width: '100%', borderRadius: 0, borderBottom: downloadsOpen ? '1.5px solid var(--border-light)' : 'none', transition: 'background 0.2s'}}
                      onClick={() => setDownloadsOpen(o => !o)}
                      aria-expanded={downloadsOpen}
                    >
                      <Download size={18} style={{verticalAlign: 'middle'}}/>
                      {strings.downloadSectionTitle || 'Descargas'}
                      <span style={{flex: 1}}/>
                      {downloadsOpen ? <ChevronUp size={20} style={{marginLeft: 6}}/> : <ChevronDown size={20} style={{marginLeft: 6}}/>}
                    </button>
                    <div style={{maxHeight: downloadsOpen ? 600 : 0, overflow: 'hidden', transition: 'max-height 0.3s cubic-bezier(.4,0,.2,1)'}}>
                      <DownloadSection
                        open={downloadsOpen}
                        onToggle={() => setDownloadsOpen(o => !o)}
                        files={selectedModel.files}
                        loadingFiles={selectedModel.loadingFiles}
                        downloadStatus={downloadStatus}
                        handleDownload={handleDownload}
                        strings={strings}
                        hasVision={hasVision}
                      />
                    </div>
                  </div>
                  {/* Sección README con cabecera desplegable e icono, colapsable visualmente */}
                  <div className={`readme-section collapsible-section${showReadme ? ' open' : ''}`} style={{borderRadius: 12, boxShadow: showReadme ? '0 2px 12px #0001' : 'none', background: showReadme ? 'rgba(135,206,235,0.07)' : 'transparent', marginBottom: 0, overflow: 'hidden', transition: 'all 0.25s'}}> 
                    <button
                      className="section-toggle-title"
                      style={{margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: '18px 0 18px 0', outline: 'none', display: 'flex', alignItems: 'center', gap: 8, width: '100%', borderRadius: 0, borderBottom: showReadme ? '1.5px solid var(--border-light)' : 'none', transition: 'background 0.2s'}}
                      onClick={() => setShowReadme(o => !o)}
                      aria-expanded={showReadme}
                    >
                      <Star size={18} style={{verticalAlign: 'middle'}}/>
                      {strings.readmeSectionTitle || 'Readme'}
                      <span style={{flex: 1}}/>
                      {showReadme ? <ChevronUp size={20} style={{marginLeft: 6}}/> : <ChevronDown size={20} style={{marginLeft: 6}}/>}
                    </button>
                    <div style={{maxHeight: showReadme ? 800 : 0, overflow: 'hidden', transition: 'max-height 0.3s cubic-bezier(.4,0,.2,1)'}}>
                      <ReadmeSection
                        open={showReadme}
                        onToggle={() => setShowReadme(o => !o)}
                        readmeHtml={readmeHtml}
                        loading={readmeLoading}
                        error={readmeError}
                        strings={strings}
                      />
                    </div>
                  </div>
                </section>
              )}
            </main>
          </div>
        </div>
      </div>
    ) : null
  );
};

export default FunctionalLMStudioDownloader;
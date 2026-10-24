import { useEffect, useRef, useState } from 'react';
import { BookOpen, X, ArrowUpRight } from 'lucide-react';
import { api } from './api';
import Catalog from './components/Catalog';
import Conversation from './components/Conversation';

export default function App() {
  const [health,setHealth]=useState(null);
  const [document,setDocument]=useState(null);
  const [docError,setDocError]=useState('');
  const dialog=useRef(null);
  useEffect(()=>{api('/health').then(setHealth).catch(()=>setHealth({configured:false,message:'Inicia el servidor local para conectar la biblioteca.'}));},[]);
  async function openDocument(source) {
    setDocument(source); setDocError(''); dialog.current.showModal();
    try {const complete=await api(`/documents/${encodeURIComponent(source.id)}`); setDocument(complete);}
    catch(error){setDocError(error.message);}
  }
  return <>
    <header className="masthead"><a className="wordmark" href="#catalogo" aria-label="UMBRA, inicio">UMBRA</a><nav aria-label="Principal"><a href="#catalogo">Catálogo</a><a href="#librero">El librero</a></nav><BookOpen size={22} aria-hidden="true"/></header>
    <main className="library-shell">
      <Catalog onOpen={openDocument}/>
      <Conversation health={health} onOpen={openDocument}/>
    </main>
    <dialog ref={dialog} className="reading-room" onClick={e=>{if(e.target===dialog.current)dialog.current.close();}}>
      <button className="icon-button close" onClick={()=>dialog.current.close()} aria-label="Cerrar documento"><X/></button>
      <p className="reading-label">SALA DE LECTURA · {document?.id}</p><h2>{document?.title}</h2>
      <p className="reading-notice">Texto disponible en TREC-COVID. Puede ser un resumen, no el artículo completo. No implica evidencia clínica actual.</p>
      {docError&&<p role="alert">{docError}</p>}<div className="document-text">{document?.text}</div>
      <a className="external-link" href={`https://scholar.google.com/scholar?q=${encodeURIComponent(document?.title||'')}`} target="_blank" rel="noreferrer">Buscar este título en Google Scholar <ArrowUpRight size={15}/></a>
    </dialog>
  </>;
}

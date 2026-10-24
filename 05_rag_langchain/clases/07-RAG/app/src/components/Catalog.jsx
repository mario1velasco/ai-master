import { useState } from 'react';
import { Search, ArrowRight, Brain, Microscope, Globe2, BookOpen } from 'lucide-react';
import { api } from '../api';
const sections=[{name:'Neurología',query:'neurological',text:'Sistema nervioso, mecanismos y manifestaciones clínicas.',Icon:Brain},
{name:'Inmunología',query:'immune response',text:'Respuesta inmune, mecanismos de defensa y enfermedad.',Icon:Microscope},
{name:'Salud pública',query:'public health',text:'Epidemiología, políticas sanitarias y salud global.',Icon:Globe2}];

export default function Catalog({onOpen}){
  const [query,setQuery]=useState(''); const [results,setResults]=useState(null);
  const [loading,setLoading]=useState(false); const [error,setError]=useState('');
  async function search(value=query){setLoading(true);setError('');try{const r=await api(`/catalog?q=${encodeURIComponent(value)}`);setResults(r.documents);}catch(e){setError(e.message);}finally{setLoading(false);}}
  return <section className="catalog" id="catalogo" aria-labelledby="catalog-title">
    <div className="catalog-inner"><h1 id="catalog-title">Toda respuesta<br/>empieza con una<br/><em>buena pregunta.</em></h1>
      <p className="intro">Explora la colección. Conversa con sus fuentes.</p>
      <form className="catalog-search" onSubmit={e=>{e.preventDefault();search();}}><Search size={21}/><input aria-label="Buscar en el catálogo" maxLength={150} placeholder="Buscar en el catálogo…" value={query} onChange={e=>setQuery(e.target.value)}/><button disabled={loading} aria-label="Buscar artículos"><ArrowRight size={19}/></button></form>
      <div className="catalog-heading"><h2>Catálogo de investigación</h2><button onClick={()=>{if(results){setResults(null);setQuery('');}else search('');}}>{results?'Volver a temas':'Ver artículos'} <ArrowRight size={14}/></button></div>
      {error&&<p className="error" role="alert">{error}</p>}
      <div aria-live="polite">{loading?<p className="catalog-loading">Abriendo el catálogo…</p>:results!==null?<>
        <p className="small-note">Búsqueda literal local · {results.length} resultados mostrados</p>
        {results.length===0?<p>No hay coincidencias. Prueba términos en inglés o consulta al librero.</p>:<div className="article-list">{results.map((doc,i)=><button className="catalog-row article" key={doc.id} onClick={()=>onOpen(doc)}><span className="row-number">{String(i+1).padStart(2,'0')}</span><BookOpen size={23}/><span><strong>{doc.title}</strong><small>{doc.text.slice(0,110)}…</small></span><ArrowRight size={17}/></button>)}</div>}</>:
        <div>{sections.map(({name,query:q,text,Icon},i)=><button className="catalog-row" key={name} onClick={()=>{setQuery(q);search(q);}}><span className="row-number">{['I','II','III'][i]}</span><span className="topic-engraving"><Icon size={42} strokeWidth={.8}/></span><span><strong>{name}</strong><small>{text}</small></span><ArrowRight size={20}/></button>)}</div>}</div>
      <p className="archive-note">Un archivo científico. Muchas perspectivas.<br/>La evidencia siempre tiene la última palabra.</p>
    </div></section>;
}

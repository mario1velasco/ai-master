import { useEffect, useRef, useState } from 'react';
import { Library, Send, RotateCcw, ArrowRight, Flame, LoaderCircle } from 'lucide-react';
import { api } from '../api';
import Response from './Response';
const suggestions=['Manifestaciones neurológicas de COVID-19','Respuesta inmune y coronavirus'];

export default function Conversation({health,onOpen}){
  const [mode,setMode]=useState('standard');const [question,setQuestion]=useState('');
  const [messages,setMessages]=useState([]);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const input=useRef(null);const bottom=useRef(null);
  useEffect(()=>{if(messages.length)bottom.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[messages,busy]);
  async function ask(event){event.preventDefault(); if(!question.trim()||busy)return;
    const text=question.trim(); const history=messages.slice(-8).map(m=>({role:m.role,content:m.text.slice(0,4000)}));
    setBusy(true);setError('');setQuestion('');setMessages(prev=>[...prev,{role:'user',text}]);
    try{const result=await api('/chat',{method:'POST',body:JSON.stringify({question:text,mode,history})});setMessages(prev=>[...prev,{role:'assistant',text:result.text,result}]);}
    catch(e){setError(e.message);setQuestion(text);setMessages(prev=>prev.slice(0,-1));}
    finally{setBusy(false);input.current?.focus();}
  }
  return <section className="librarian" id="librero" aria-labelledby="librarian-title"><div className="panel-frame">
    <div className="librarian-heading"><Library size={39} strokeWidth={1}/><div><h2 id="librarian-title">El librero</h2><p>Respuestas con fuentes, no con suposiciones.</p></div>{messages.length>0&&<button className="icon-button reset" disabled={busy} aria-label="Nueva conversación" onClick={()=>{setMessages([]);setError('');setQuestion('');}}><RotateCcw size={17}/></button>}</div>
    <fieldset className="mode-selector" disabled={busy}><legend>Modo de conversación</legend><label><input type="radio" name="mode" value="standard" checked={mode==='standard'} onChange={()=>setMode('standard')}/> RAG estándar</label><label><input type="radio" name="mode" value="tools" checked={mode==='tools'} onChange={()=>setMode('tools')}/> Búsqueda como herramienta</label></fieldset>
    <div className={`conversation ${messages.length?'has-messages':''}`} aria-live="polite" aria-busy={busy}>
      {!messages.length&&<div className="welcome"><div className="candle"><Flame size={48} strokeWidth={.7}/></div><h3>¿Qué te gustaría investigar?</h3><p>Puedes hacer una pregunta en lenguaje natural<br/>o elegir una de las sugerencias.</p><div className="suggestions">{suggestions.map(text=><button key={text} onClick={()=>{setQuestion(text);input.current?.focus();}}>{text}<ArrowRight size={17}/></button>)}</div></div>}
      {messages.map((message,i)=>message.role==='user'?<div className="user-message" key={i}><span>Tú</span><p>{message.text}</p></div>:<Response key={i} result={message.result} onOpen={onOpen}/>)}
      {busy&&<p className="thinking" role="status"><LoaderCircle size={17}/> {mode==='tools'?'El librero prepara y consulta la herramienta…':'Buscando documentos y contrastando fuentes…'}</p>}<div ref={bottom}/>
    </div>
    {error&&<p className="error" role="alert">{error}</p>}
    <form className="composer" onSubmit={ask}><textarea ref={input} aria-label="Pregunta al librero" placeholder="Escribe tu pregunta…" maxLength={2000} value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask(e);}}}/><span>Enter para enviar · Shift + Enter para nueva línea</span><button disabled={busy||!question.trim()} aria-label="Enviar pregunta"><Send size={22}/></button></form>
    {health&&!health.configured&&<p className="connection-note">{health.message}</p>}
    <footer className="panel-footer"><span/> TREC-COVID · Biblioteca de investigación <span/></footer><p className="disclaimer">Evidencia histórica, no consejo médico. Las consultas usan APIs externas.</p>
  </div></section>;
}

export async function api(path, options={}) {
  const response = await fetch(`/api${path}`, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo completar la petición. Revisa el servidor local.');
  return data;
}

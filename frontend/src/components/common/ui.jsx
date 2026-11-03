import { createContext, useCallback, useContext, useState } from "react";

// ---------- Toast notifications ----------
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const notify = useCallback((message, type = "success") => {
    const id = Math.random();
    setItems((x) => [...x, { id, message, type }]);
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 4000);
  }, []);
  return (
    <ToastCtx.Provider value={notify}>
      {children}
      <div className="toasts">
        {items.map((t) => (<div key={t.id} className={`toast ${t.type}`}>{t.message}</div>))}
      </div>
    </ToastCtx.Provider>
  );
}

// ---------- Layout bits ----------
export const PageHeader = ({ title, children }) => (
  <div className="page-header"><h2>{title}</h2><div className="actions">{children}</div></div>
);

export const StatCard = ({ label, value, sub }) => (
  <div className="stat"><div className="stat-label">{label}</div><div className="stat-value">{value ?? "—"}</div>{sub && <div className="stat-sub">{sub}</div>}</div>
);

export const Loading = ({ error }) => (error ? <div className="alert">{error}</div> : <div className="muted">Loading…</div>);

export const Badge = ({ children, tone = "gray" }) => <span className={`badge ${tone}`}>{children}</span>;

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className={`modal ${wide ? "wide" : ""}`} onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head"><h3>{title}</h3><button className="btn ghost" onClick={onClose}>✕</button></div>
        {children}
      </div>
    </div>
  );
}

// ---------- Table ----------
export function DataTable({ columns, rows, empty = "No records found" }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{columns.map((c) => <th key={c.label}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows?.length ? rows.map((r, i) => (
            <tr key={r.id ?? i}>{columns.map((c) => <td key={c.label}>{c.render ? c.render(r) : r[c.key] ?? "—"}</td>)}</tr>
          )) : <tr><td colSpan={columns.length} className="muted center">{empty}</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({ page, pageSize, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="pagination">
      <button className="btn" disabled={page <= 1} onClick={() => onChange(page - 1)}>‹ Prev</button>
      <span>Page {page} of {pages} · {total} records</span>
      <button className="btn" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next ›</button>
    </div>
  );
}

// ---------- Generic form modal ----------
// fields: [{name,label,type,required,number,options,resets,createOnly,minLength}]
// options: [[value,label],...] or a function (values) => [[value,label],...]
export function FormModal({ title, fields, initial = {}, onSubmit, onClose }) {
  const editing = initial.id != null;
  const shown = fields.filter((f) => !(editing && f.createOnly));
  const [v, setV] = useState(() => Object.fromEntries(shown.map((f) => [f.name, initial[f.name] ?? ""])));
  const [busy, setBusy] = useState(false);

  const change = (f, val) => setV((p) => {
    const next = { ...p, [f.name]: val };
    (f.resets || []).forEach((n) => { next[n] = ""; });
    return next;
  });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const out = {};
    shown.forEach((f) => {
      let x = v[f.name];
      if (x === "" || x === undefined) x = null;
      else if (f.number) x = Number(x);
      out[f.name] = x;
    });
    await onSubmit(out);
    setBusy(false);
  };

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={submit} className="form-grid">
        {shown.map((f) => {
          const opts = typeof f.options === "function" ? f.options(v) : f.options;
          return (
            <label key={f.name} className={f.type === "textarea" ? "full" : ""}>
              <span>{f.label}{f.required && " *"}</span>
              {f.type === "select" ? (
                <select value={v[f.name]} required={f.required} onChange={(e) => change(f, e.target.value)}>
                  <option value="">— select —</option>
                  {opts.map(([val, label]) => <option key={val} value={val}>{label}</option>)}
                </select>
              ) : f.type === "textarea" ? (
                <textarea rows={2} value={v[f.name]} onChange={(e) => change(f, e.target.value)} />
              ) : (
                <input type={f.type || "text"} value={v[f.name]} required={f.required} minLength={f.minLength}
                  step={f.step} min={f.min} onChange={(e) => change(f, e.target.value)} />
              )}
            </label>
          );
        })}
        <div className="full modal-actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
        </div>
      </form>
    </Modal>
  );
}

// ---------- Generic CRUD page (departments, courses, subjects) ----------
import api, { errMsg } from "../../services/api";
import { useEffect } from "react";

export function CrudPage({ title, endpoint, columns, fields, initialNew = {} }) {
  const [rows, setRows] = useState([]);
  const [modal, setModal] = useState(null);
  const notify = useToast();

  const load = () => api.get(endpoint).then((r) => setRows(r.data)).catch((e) => notify(errMsg(e), "error"));
  useEffect(() => { load(); }, [endpoint]); // eslint-disable-line

  const save = async (vals) => {
    try {
      if (modal.id) await api.put(`${endpoint}/${modal.id}`, vals); else await api.post(endpoint, vals);
      notify("Saved successfully"); setModal(null); load();
    } catch (e) { notify(errMsg(e), "error"); }
  };
  const remove = async (r) => {
    if (!window.confirm("Delete this record? This cannot be undone.")) return;
    try { await api.delete(`${endpoint}/${r.id}`); notify("Deleted"); load(); } catch (e) { notify(errMsg(e), "error"); }
  };

  return (
    <>
      <PageHeader title={title}><button className="btn primary" onClick={() => setModal({ ...initialNew })}>+ Add</button></PageHeader>
      <DataTable rows={rows} columns={[...columns, { label: "Actions", render: (r) => (
        <div className="row-actions"><button className="btn sm" onClick={() => setModal(r)}>Edit</button><button className="btn sm danger" onClick={() => remove(r)}>Delete</button></div>) }]} />
      {modal && <FormModal title={modal.id ? `Edit ${title}` : `Add ${title}`} fields={fields} initial={modal} onSubmit={save} onClose={() => setModal(null)} />}
    </>
  );
}

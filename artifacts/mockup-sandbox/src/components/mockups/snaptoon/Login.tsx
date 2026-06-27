export function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#0D1017", fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        input { outline: none; }
        input:focus { border-color: #F59E0B !important; box-shadow: 0 0 0 3px rgba(245,158,11,.12) !important; }
        .btn-primary { background: #F59E0B; border: none; color: #0D1017; font-weight: 600; font-size: 14px; padding: 10px 0; border-radius: 6px; cursor: pointer; width: 100%; transition: background .15s; }
        .btn-primary:hover { background: #FBBF24; }
      `}</style>

      <div style={{ width: 380, background: "#161B26", border: "1px solid #1E2436", borderRadius: 12, padding: "2.5rem 2rem" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ fontSize: "2.25rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.04em", lineHeight: 1 }}>
            SnapToon<span style={{ display: "inline-block", width: 7, height: 7, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 6 }} />
          </div>
          <div style={{ fontSize: 13, color: "#64748B", marginTop: 6, fontStyle: "italic" }}>
            Dall'idea al fumetto, in uno snap.
          </div>
        </div>

        {/* Form */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#94A3B8", marginBottom: 5, textTransform: "uppercase", letterSpacing: ".06em" }}>Email</label>
            <input
              type="email"
              placeholder="nome@dominio.com"
              style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 14 }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#94A3B8", marginBottom: 5, textTransform: "uppercase", letterSpacing: ".06em" }}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 14 }}
            />
          </div>
          <button className="btn-primary" style={{ marginTop: 4 }}>Accedi</button>
          <p style={{ textAlign: "center", fontSize: 12, color: "#475569", margin: 0 }}>
            Hai dimenticato la password? Contatta l'amministratore.
          </p>
        </div>
      </div>
    </div>
  );
}

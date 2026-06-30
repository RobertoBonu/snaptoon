import React, { useState, useEffect } from "react";
import { ArrowRight, ChevronRight, Menu, Zap, Play, PlayCircle, BookOpen, Layers, LayoutTemplate, BoxSelect, Sparkles, Settings2, Code2 } from "lucide-react";

export function Landing() {
  return (
    <div style={{ backgroundColor: "#0D1017", minHeight: "100vh", fontFamily: "'Inter', sans-serif", color: "#E2E8F0", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        
        /* Typography utilities */
        .text-primary { color: #F1F5F9; }
        .text-secondary { color: #94A3B8; }
        .text-tertiary { color: #64748B; }
        .text-amber { color: #F59E0B; }
        
        /* Button styles */
        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; font-weight: 600; padding: 10px 20px; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; border: none; }
        .btn-primary { background: #F59E0B; color: #0D1017; }
        .btn-primary:hover { background: #FBBF24; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2); }
        .btn-secondary { background: transparent; border: 1px solid #2D3748; color: #E2E8F0; }
        .btn-secondary:hover { background: #161B26; border-color: #475569; }
        .btn-ghost { background: transparent; color: #94A3B8; padding: 8px 16px; }
        .btn-ghost:hover { color: #F1F5F9; background: rgba(255,255,255,0.05); }

        /* Animation utilities */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fadeIn 0.8s ease forwards; }
        
        /* Layout utilities */
        .container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }
        .section { padding: 100px 0; }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0D1017; }
        ::-webkit-scrollbar-thumb { background: #1E2436; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #2D3748; }

        /* Product Cards */
        .product-card { background: #161B26; border: 1px solid #1E2436; border-radius: 16px; overflow: hidden; transition: all 0.3s ease; display: flex; flex-direction: column; }
        .product-card:hover { border-color: #2D3748; transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
        
        /* Node Editor */
        .node-card { background: #161B26; border: 1px solid #2D3748; border-radius: 12px; padding: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 10; position: relative; width: 280px; }
        .node-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid #1E2436; padding-bottom: 12px; }
        .node-port { width: 10px; height: 10px; background: #0D1017; border: 2px solid #64748B; border-radius: 50%; position: absolute; top: 50%; transform: translateY(-50%); }
        .node-port.in { left: -6px; }
        .node-port.out { right: -6px; border-color: #F59E0B; }
        .node-port.out.active { background: #F59E0B; box-shadow: 0 0 8px #F59E0B; }
      `}</style>

      <Header />
      
      <main>
        <HeroSection />
        <ProductsSection />
        <WorkflowSection />
      </main>

      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header style={{ position: "sticky", top: 0, zIndex: 100, background: "rgba(13, 16, 23, 0.85)", backdropFilter: "blur(12px)", borderBottom: "1px solid #1E2436" }}>
      <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: "72px" }}>
        
        <div style={{ display: "flex", alignItems: "center", gap: "48px" }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
            <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
              SnapToon
            </span>
            <span style={{ display: "inline-block", width: 8, height: 8, background: "#7C3AED", borderRadius: "50%", marginLeft: 4, marginBottom: 6 }} />
          </div>

          {/* Desktop Nav */}
          <nav style={{ display: "none", alignItems: "center", gap: "8px" }} className="md-flex">
            {["SnapToon", "Crea", "Esplora", "Pricing"].map((item) => (
              <a key={item} style={{ fontSize: "14px", fontWeight: 500, color: "#94A3B8", padding: "8px 16px", borderRadius: "6px", cursor: "pointer", transition: "color 0.2s" }} onMouseOver={(e) => e.currentTarget.style.color = "#F1F5F9"} onMouseOut={(e) => e.currentTarget.style.color = "#94A3B8"}>
                {item}
              </a>
            ))}
          </nav>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="btn btn-secondary" style={{ padding: "8px 16px" }}>Accedi</button>
          <button className="btn btn-primary" style={{ padding: "8px 16px" }}>Prova SnapToon</button>
        </div>

      </div>
      <style>{`
        @media (min-width: 768px) {
          .md-flex { display: flex !important; }
        }
      `}</style>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="section" style={{ position: "relative", overflow: "hidden", paddingTop: "120px", paddingBottom: "120px" }}>
      {/* Background Gradients */}
      <div style={{ position: "absolute", top: "-20%", left: "50%", transform: "translateX(-50%)", width: "80%", height: "80%", background: "radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, rgba(13, 16, 23, 0) 70%)", zIndex: 0, pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: "20%", right: "-10%", width: "40%", height: "60%", background: "radial-gradient(circle, rgba(124, 58, 237, 0.05) 0%, rgba(13, 16, 23, 0) 70%)", zIndex: 0, pointerEvents: "none" }} />

      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        <div style={{ textAlign: "center", maxWidth: "800px", margin: "0 auto", marginBottom: "64px" }}>
          <div className="animate-fade-in" style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.2)", padding: "6px 12px", borderRadius: "100px", color: "#F59E0B", fontSize: "13px", fontWeight: 600, marginBottom: "24px" }}>
            <Sparkles size={14} />
            <span>Nuovo motore di generazione V2 disponibile</span>
          </div>
          
          <h1 className="animate-fade-in" style={{ fontSize: "clamp(3rem, 5vw, 4.5rem)", fontWeight: 800, color: "#F1F5F9", lineHeight: 1.1, letterSpacing: "-0.03em", marginBottom: "24px", animationDelay: "0.1s" }}>
            Dall'idea al fumetto,<br />in uno <span style={{ color: "#F59E0B" }}>snap.</span>
          </h1>
          
          <p className="animate-fade-in" style={{ fontSize: "1.125rem", color: "#94A3B8", lineHeight: 1.6, marginBottom: "40px", animationDelay: "0.2s", maxWidth: "640px", margin: "0 auto 40px auto" }}>
            Il primo studio creativo AI desktop-first che trasforma testi, sceneggiature e idee in tavole a fumetti professionali. Senza saper disegnare, con il pieno controllo.
          </p>
          
          <div className="animate-fade-in" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "16px", animationDelay: "0.3s" }}>
            <button className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>
              Inizia gratis <ArrowRight size={18} />
            </button>
            <button className="btn btn-secondary" style={{ padding: "14px 28px", fontSize: "15px" }}>
              <PlayCircle size={18} /> Guarda come funziona
            </button>
          </div>
        </div>

        {/* Hero Visual */}
        <div className="animate-fade-in" style={{ animationDelay: "0.4s", position: "relative", borderRadius: "24px", padding: "8px", background: "linear-gradient(180deg, rgba(30, 36, 54, 0.5) 0%, rgba(13, 16, 23, 0) 100%)", border: "1px solid rgba(45, 55, 72, 0.5)", borderTopColor: "rgba(245, 158, 11, 0.3)", boxShadow: "0 24px 64px rgba(0,0,0,0.4)" }}>
          <div style={{ borderRadius: "16px", overflow: "hidden", aspectRatio: "16/9", background: "#0A0E17", position: "relative" }}>
            <img 
              src="/__mockup/images/hero-comic.png" 
              alt="SnapToon Hero Collage" 
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              onError={(e) => {
                e.currentTarget.src = "";
                e.currentTarget.style.background = "#161B26";
              }}
            />
            {/* UI Overlay mock */}
            <div style={{ position: "absolute", bottom: "24px", left: "24px", right: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
              <div style={{ background: "rgba(13, 16, 23, 0.8)", backdropFilter: "blur(8px)", padding: "16px", borderRadius: "12px", border: "1px solid #2D3748", maxWidth: "320px" }}>
                <div style={{ fontSize: "12px", color: "#F59E0B", fontWeight: 600, marginBottom: "4px", textTransform: "uppercase" }}>Generazione completata</div>
                <div style={{ fontSize: "14px", color: "#F1F5F9" }}>Tavola 1: Introduzione nella metropoli cyber-punk...</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}

function ProductsSection() {
  const cards = [
    {
      title: "LA TUA IDEA",
      desc: "Adatta soggetto, sceneggiatura e dialoghi senza inventare nulla",
      img: "/__mockup/images/card-generator.png",
      actions: ["Prova ora"]
    },
    {
      title: "Stili Artistici",
      desc: "Manga, Cartoon, Noir, Acquerello e molto altro.",
      img: "/__mockup/images/card-styles.png",
      actions: ["Prova ora", "Scopri di più"]
    },
    {
      title: "Personaggi Coerenti",
      desc: "Mantieni i tuoi personaggi identici in ogni vignetta.",
      img: "/__mockup/images/card-characters.png",
      actions: ["Prova ora", "Scopri di più"]
    },
    {
      title: "Impaginazione Smart",
      desc: "Layout automatici per vignette e baloon.",
      img: "/__mockup/images/card-layout.png",
      actions: ["Prova ora", "Scopri di più"]
    }
  ];

  return (
    <section className="section" style={{ background: "#0A0E17", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436" }}>
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: "64px", maxWidth: "800px", margin: "0 auto 64px auto" }}>
          <h2 style={{ fontSize: "clamp(2rem, 3vw, 2.5rem)", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", marginBottom: "16px" }}>
            Tutto ciò che ti serve per trasformare la tua creatività in un fumetto.
          </h2>
          <p style={{ fontSize: "1.125rem", color: "#94A3B8" }}>
            I nostri ultimi modelli e strumenti
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px" }}>
          {cards.map((card, idx) => (
            <div key={idx} className="product-card">
              <div style={{ aspectRatio: "4/3", overflow: "hidden", background: "#0D1017", borderBottom: "1px solid #1E2436" }}>
                <img 
                  src={card.img} 
                  alt={card.title}
                  style={{ width: "100%", height: "100%", objectFit: "cover", transition: "transform 0.5s ease" }}
                  onMouseOver={(e) => e.currentTarget.style.transform = "scale(1.05)"}
                  onMouseOut={(e) => e.currentTarget.style.transform = "scale(1)"}
                  onError={(e) => {
                    e.currentTarget.src = "";
                    e.currentTarget.style.background = "#161B26";
                  }}
                />
              </div>
              <div style={{ padding: "24px", display: "flex", flexDirection: "column", flex: 1 }}>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "#F1F5F9", marginBottom: "8px" }}>{card.title}</h3>
                <p style={{ fontSize: "0.875rem", color: "#94A3B8", lineHeight: 1.5, marginBottom: "24px", flex: 1 }}>{card.desc}</p>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button className="btn btn-secondary" style={{ padding: "8px 16px", fontSize: "13px", flex: card.actions.length === 1 ? 1 : "auto" }}>
                    {card.actions[0]}
                  </button>
                  {card.actions[1] && (
                    <button className="btn btn-ghost" style={{ padding: "8px 12px", fontSize: "13px" }}>
                      {card.actions[1]}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function WorkflowSection() {
  return (
    <section className="section" style={{ position: "relative", overflow: "hidden" }}>
      {/* Grid Background */}
      <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(rgba(30, 36, 54, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 36, 54, 0.3) 1px, transparent 1px)", backgroundSize: "40px 40px", zIndex: 0, opacity: 0.5 }} />

      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        <div style={{ textAlign: "center", marginBottom: "64px" }}>
          <h2 style={{ fontSize: "clamp(2rem, 3vw, 2.75rem)", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", marginBottom: "16px", maxWidth: "600px", margin: "0 auto 16px auto", lineHeight: 1.1 }}>
            Costruisci i Workflow<br />su Misura per Te
          </h2>
          <p style={{ fontSize: "1.125rem", color: "#94A3B8", maxWidth: "640px", margin: "0 auto 32px auto" }}>
            Crea flussi personalizzati che collegano più modelli e passaggi intermedi per il pieno controllo delle tue creazioni.
          </p>
          <button className="btn" style={{ background: "transparent", border: "1px solid #F59E0B", color: "#F59E0B", borderRadius: "100px", padding: "10px 24px" }}>
            Scopri di più sui Workflow
          </button>
        </div>

        {/* Node Diagram Canvas */}
        <div style={{ height: "600px", position: "relative", background: "rgba(10, 14, 23, 0.6)", border: "1px solid #1E2436", borderRadius: "24px", backdropFilter: "blur(8px)", overflow: "hidden" }}>
          
          {/* SVG Connections */}
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
            <defs>
              <linearGradient id="wireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#475569" />
                <stop offset="50%" stopColor="#7C3AED" />
                <stop offset="100%" stopColor="#F59E0B" />
              </linearGradient>
            </defs>
            {/* Wires */}
            <path d="M 260 180 C 290 180, 290 120, 320 120" fill="none" stroke="#475569" strokeWidth="2" />
            <path d="M 260 250 C 290 250, 290 300, 320 300" fill="none" stroke="#475569" strokeWidth="2" />
            <path d="M 600 120 C 615 120, 615 210, 630 210" fill="none" stroke="#475569" strokeWidth="2" />
            <path d="M 600 300 C 615 300, 615 210, 630 210" fill="none" stroke="#475569" strokeWidth="2" />
            
            <path d="M 910 210 C 925 210, 925 320, 940 320" fill="none" stroke="url(#wireGrad)" strokeWidth="3" className="animated-wire" />
          </svg>

          {/* Nodes */}
          {/* Node 1: Testo */}
          <div className="node-card" style={{ position: "absolute", top: "150px", left: "20px" }}>
            <div className="node-header">
              <BookOpen size={16} color="#F59E0B" />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9" }}>Input: Testo</span>
            </div>
            <div style={{ background: "#0D1017", padding: "12px", borderRadius: "6px", fontSize: "12px", color: "#94A3B8", fontFamily: "monospace", border: "1px solid #1E2436" }}>
              "La città di Neo-Roma era avvolta dalla nebbia di smog e neon..."
            </div>
            <div className="node-port out active" style={{ top: "180px" }}></div>
            <div className="node-port out active" style={{ top: "250px" }}></div>
          </div>

          {/* Node 2: Stile */}
          <div className="node-card" style={{ position: "absolute", top: "60px", left: "320px" }}>
            <div className="node-port in"></div>
            <div className="node-header">
              <Settings2 size={16} color="#7C3AED" />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9" }}>Configura Stile</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#0D1017", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1E2436", marginBottom: "8px" }}>
              <span style={{ fontSize: "12px", color: "#94A3B8" }}>Modello</span>
              <span style={{ fontSize: "12px", color: "#F1F5F9", fontWeight: 500 }}>Fumetto V2</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#0D1017", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1E2436" }}>
              <span style={{ fontSize: "12px", color: "#94A3B8" }}>Inchiostrazione</span>
              <span style={{ fontSize: "12px", color: "#F1F5F9", fontWeight: 500 }}>Nera pesante</span>
            </div>
            <div className="node-port out active"></div>
          </div>

          {/* Node 3: Personaggi */}
          <div className="node-card" style={{ position: "absolute", top: "240px", left: "320px" }}>
            <div className="node-port in"></div>
            <div className="node-header">
              <BoxSelect size={16} color="#10B981" />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9" }}>Cast Personaggi</span>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "4px", background: "#2D3748" }}></div>
              <div style={{ width: "40px", height: "40px", borderRadius: "4px", background: "#2D3748" }}></div>
              <div style={{ width: "40px", height: "40px", borderRadius: "4px", background: "#1E2436", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748B", fontSize: "16px" }}>+</div>
            </div>
            <div className="node-port out active"></div>
          </div>

          {/* Node 4: Genera */}
          <div className="node-card" style={{ position: "absolute", top: "120px", left: "630px", borderColor: "#F59E0B", boxShadow: "0 0 0 1px rgba(245, 158, 11, 0.2), 0 8px 32px rgba(245, 158, 11, 0.1)" }}>
            <div className="node-port in" style={{ top: "90px" }}></div>
            <div className="node-header" style={{ borderBottomColor: "rgba(245,158,11,0.2)" }}>
              <Zap size={16} color="#F59E0B" />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "#F59E0B" }}>Genera Tavola</span>
            </div>
            <div style={{ width: "100%", height: "140px", background: "#0D1017", borderRadius: "8px", overflow: "hidden", border: "1px solid #2D3748" }}>
              <img src="/__mockup/images/card-generator.png" alt="Generazione" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.8 }} onError={(e) => e.currentTarget.style.display = 'none'} />
            </div>
            <div className="node-port out active"></div>
          </div>

          {/* Node 5: Impagina */}
          <div className="node-card" style={{ position: "absolute", top: "240px", left: "940px" }}>
            <div className="node-port in"></div>
            <div className="node-header">
              <LayoutTemplate size={16} color="#3B82F6" />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9" }}>Impaginazione Smart</span>
            </div>
            <div style={{ width: "100%", height: "100px", background: "#0D1017", borderRadius: "8px", overflow: "hidden", border: "1px solid #2D3748" }}>
              <img src="/__mockup/images/card-layout.png" alt="Impaginazione" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.8 }} onError={(e) => e.currentTarget.style.display = 'none'} />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer style={{ background: "#0A0E17", borderTop: "1px solid #1E2436", paddingTop: "80px", paddingBottom: "40px" }}>
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "64px", marginBottom: "64px" }}>
          
          <div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "16px" }}>
              <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
                SnapToon
              </span>
              <span style={{ display: "inline-block", width: 8, height: 8, background: "#7C3AED", borderRadius: "50%", marginLeft: 4, marginBottom: 6 }} />
            </div>
            <p style={{ fontSize: "14px", color: "#64748B", maxWidth: "300px", lineHeight: 1.6 }}>
              L'AI studio per creatori di fumetti. Trasforma le tue storie in tavole illustrate professionali con il pieno controllo artistico.
            </p>
          </div>

          <div>
            <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "20px" }}>Prodotto</h4>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
              {["Funzionalità", "Modelli AI", "Workflow", "Pricing", "Changelog"].map(link => (
                <li key={link}><a href="#" style={{ color: "#94A3B8", fontSize: "14px", textDecoration: "none", transition: "color 0.2s" }} onMouseOver={(e) => e.currentTarget.style.color = "#F59E0B"} onMouseOut={(e) => e.currentTarget.style.color = "#94A3B8"}>{link}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "20px" }}>Risorse</h4>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
              {["Documentazione", "Tutorial", "Community", "Stili Pubblici", "Blog"].map(link => (
                <li key={link}><a href="#" style={{ color: "#94A3B8", fontSize: "14px", textDecoration: "none", transition: "color 0.2s" }} onMouseOver={(e) => e.currentTarget.style.color = "#F59E0B"} onMouseOut={(e) => e.currentTarget.style.color = "#94A3B8"}>{link}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "20px" }}>Azienda & Legale</h4>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
              {["Chi Siamo", "Contatti", "Privacy Policy", "Termini di Servizio"].map(link => (
                <li key={link}><a href="#" style={{ color: "#94A3B8", fontSize: "14px", textDecoration: "none", transition: "color 0.2s" }} onMouseOver={(e) => e.currentTarget.style.color = "#F59E0B"} onMouseOut={(e) => e.currentTarget.style.color = "#94A3B8"}>{link}</a></li>
              ))}
            </ul>
          </div>

        </div>

        <div style={{ borderTop: "1px solid #1E2436", paddingTop: "32px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ fontSize: "13px", color: "#64748B" }}>
            © 2026 SnapToon. Tutti i diritti riservati.
          </div>
          <div style={{ display: "flex", gap: "16px" }}>
            {["Twitter", "Discord", "Instagram"].map(social => (
              <a key={social} href="#" style={{ fontSize: "13px", color: "#64748B", textDecoration: "none", transition: "color 0.2s" }} onMouseOver={(e) => e.currentTarget.style.color = "#F1F5F9"} onMouseOut={(e) => e.currentTarget.style.color = "#64748B"}>{social}</a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

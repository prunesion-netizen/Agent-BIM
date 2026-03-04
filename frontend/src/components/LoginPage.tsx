import { useState, type FormEvent } from "react";
import { useAuth } from "../contexts/AuthProvider";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, username, password);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare necunoscuta");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">Agent BIM</div>
          <p className="login-subtitle">Management BIM conform ISO 19650</p>
        </div>

        <div className="login-toggle">
          <button
            className={`login-toggle-btn ${!isRegister ? "active" : ""}`}
            onClick={() => { setIsRegister(false); setError(null); }}
          >
            Autentificare
          </button>
          <button
            className={`login-toggle-btn ${isRegister ? "active" : ""}`}
            onClick={() => { setIsRegister(true); setError(null); }}
          >
            Cont nou
          </button>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@exemplu.ro"
              required
              autoFocus
            />
          </div>

          {isRegister && (
            <div className="login-field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="utilizator"
                required
                minLength={3}
              />
            </div>
          )}

          <div className="login-field">
            <label htmlFor="password">Parola</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="minim 6 caractere"
              required
              minLength={6}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button
            type="submit"
            className="login-submit"
            disabled={loading}
          >
            {loading
              ? "Se proceseaza..."
              : isRegister
                ? "Creaza cont"
                : "Intra in cont"}
          </button>
        </form>
      </div>
    </div>
  );
}

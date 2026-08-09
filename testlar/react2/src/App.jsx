import { Sparkles, Rocket, ShieldCheck } from 'lucide-react';

const features = [
  {
    title: 'Fast setup',
    description: 'Start building immediately with a modern Vite scaffold.',
    icon: Rocket,
  },
  {
    title: 'Modern UI',
    description: 'A polished dark theme with clean spacing and strong contrast.',
    icon: Sparkles,
  },
  {
    title: 'Production ready',
    description: 'Structured for growth and easy collaboration.',
    icon: ShieldCheck,
  },
];

export default function App() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <p className="eyebrow">Scode React + Vite</p>
        <h1>Build your next idea with confidence.</h1>
        <p className="hero-copy">
          This starter includes a modern layout, reusable components, and a clean development setup.
        </p>
        <div className="feature-grid">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article className="feature-card" key={feature.title}>
                <Icon size={20} />
                <h2>{feature.title}</h2>
                <p>{feature.description}</p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

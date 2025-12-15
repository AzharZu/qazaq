export function Footer() {
  return (
    <footer className="mt-12 border-t border-slate-200 bg-[#e5e5e5]">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4 text-sm text-slate-700">
        <span>© 2025</span>
        <div className="flex items-center gap-6">
          <a href="#" className="hover:text-slate-900">
            О нас
          </a>
          <a href="#" className="hover:text-slate-900">
            Контакты
          </a>
          <a href="#" className="hover:text-slate-900">
            Помощь
          </a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;

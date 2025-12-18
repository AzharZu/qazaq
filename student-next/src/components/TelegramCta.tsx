import { AnchorHTMLAttributes } from "react";

type TelegramCtaProps = {
  className?: string;
} & AnchorHTMLAttributes<HTMLAnchorElement>;

const TelegramIcon = ({ className = "h-6 w-6" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 240 240"
    className={className}
    aria-hidden="true"
    focusable="false"
  >
    <path
      fill="#229ED9"
      d="M120 0C53.7 0 0 53.7 0 120s53.7 120 120 120 120-53.7 120-120S186.3 0 120 0z"
    />
    <path
      fill="#130f35ff"
      d="m56.4 118.3 102.6-39c4.8-1.9 9.1.3 7.5 7l-17.4 82.1c-1.3 6.1-4.8 7.6-9.7 4.7l-26.8-19.7-12.9 12.4c-1.4 1.4-2.5 2.5-5 2.5l1.8-27 49.1-44.3c2.1-1.8-.5-2.9-3.3-1.1l-60.7 38.2-26.2-8.2c-5.7-1.8-5.8-5.7 1.2-8.3z"
    />
  </svg>
);

export default function TelegramCta({ className = "", ...rest }: TelegramCtaProps) {
  return (
    <section
      className={`rounded-2xl border border-slate/10 bg-white/95 p-6 shadow-card transition hover:shadow-2xl md:p-7 ${className}`}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#e8f4ff] shadow-inner">
            <TelegramIcon />
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-semibold text-slateDeep">Учи казахские слова где угодно 📱</h3>
            <p className="text-sm text-slate-700">
              Перейди в наш Telegram-бот и практикуй слова каждый день — быстро и удобно.
              <span className="block text-slate-600">Telegram-ботта сөздерді кез келген жерде үйрен!</span>
            </p>
          </div>
        </div>
        <a
          {...rest}
          href="https://t.me/qazaqqie_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 self-start rounded-xl bg-[#229ED9] px-4 py-3 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 hover:bg-[#1f8cc6]"
        >
          <TelegramIcon className="h-5 w-5" />
          🚀 Перейти в Telegram-бот
        </a>
      </div>
    </section>
  );
}

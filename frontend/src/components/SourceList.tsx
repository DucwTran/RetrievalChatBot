import { Image as ImageIcon } from "lucide-react";
import type { Source } from "../lib/api";

const MAX_SOURCES = 3;

export default function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  const shown = sources.slice(0, MAX_SOURCES);

  return (
    <div className="mt-3 border-t border-gray-100 pt-2">
      <p className="mb-1.5 text-xs font-medium text-gray-500">Nguồn tham khảo</p>
      <ul className="space-y-2">
        {shown.map((source, i) => (
          <li key={i} className="overflow-hidden rounded-lg border border-gray-200 text-xs">
            {source.image_url && (
              <img
                src={source.image_url}
                alt={source.title}
                loading="lazy"
                className="h-32 w-full object-cover"
                onError={(e) => (e.currentTarget.style.display = "none")}
              />
            )}
            <div className="bg-gray-50 p-2">
              <p className="flex items-center gap-1 font-medium text-gray-700">
                {source.image_url && <ImageIcon className="h-3 w-3" />}
                <span>
                  [{i + 1}] {source.title}
                </span>
              </p>
              <p className="mt-0.5 line-clamp-2 text-gray-500">{source.snippet}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

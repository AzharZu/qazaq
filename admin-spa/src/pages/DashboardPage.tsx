import { useEffect, useState } from "react";
import { Card, CardContent, CardTitle } from "../components/ui/card";
import { coursesApi, lessonsApi, modulesApi, vocabularyApi } from "../api/entities";

export default function DashboardPage() {
  const [counts, setCounts] = useState({ courses: 0, modules: 0, lessons: 0, vocab: 0 });

  useEffect(() => {
    async function fetchCounts() {
      try {
        const [courses, mods, lessons, vocab] = await Promise.all([
          coursesApi.list(),
          modulesApi.list(),
          lessonsApi.list(),
          vocabularyApi.list(),
        ]);
        setCounts({ courses: courses.length, modules: mods.length, lessons: lessons.length, vocab: vocab.length });
      } catch {
        // ignore
      }
    }
    fetchCounts();
  }, []);

  const items = [
    { label: "Courses", value: counts.courses },
    { label: "Modules", value: counts.modules },
    { label: "Lessons", value: counts.lessons },
    { label: "Vocabulary", value: counts.vocab },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardTitle>{item.label}</CardTitle>
          <CardContent>
            <div className="text-3xl font-bold mt-2">{item.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

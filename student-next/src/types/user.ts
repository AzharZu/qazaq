export interface User {
  id: number;
  email: string;
  role?: string;
  age?: number;
  target?: string;
  daily_minutes?: number;
  level?: string | null;
  name?: string;
}

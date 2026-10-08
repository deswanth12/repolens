import { UserModel } from './models';

export function getRoutes(): string[] {
  const u = new UserModel("admin");
  return ["/api/v1", `/users/${u.username}`];
}

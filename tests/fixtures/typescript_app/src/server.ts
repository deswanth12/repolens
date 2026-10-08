import { getRoutes } from './routes';

export class Server {
  public start(): void {
    const routes = getRoutes();
    console.log("Registered routes:", routes);
  }
}

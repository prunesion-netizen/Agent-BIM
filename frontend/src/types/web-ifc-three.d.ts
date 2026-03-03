declare module "web-ifc-three" {
  import { Loader, Object3D } from "three";

  export class IFCManager {
    setWasmPath(path: string, absolute?: boolean): void;
    parse(data: Uint8Array): Promise<Object3D>;
    applyWebIfcConfig(config: Record<string, unknown>): void;
    parser: {
      setupOptionalCategories(categories: Record<number, boolean>): void;
    };
  }

  export class IFCLoader extends Loader {
    ifcManager: IFCManager;
    load(
      url: string,
      onLoad: (model: Object3D) => void,
      onProgress?: (event: ProgressEvent) => void,
      onError?: (error: unknown) => void,
    ): void;
  }
}

declare module "web-ifc" {
  export const IFCSPACE: number;
  export const IFCOPENINGELEMENT: number;
}

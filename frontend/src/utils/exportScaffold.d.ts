export declare const PINNED_CLIENT_DEPENDENCIES: Record<string, string>;
export declare const PINNED_CLIENT_DEV_DEPENDENCIES: Record<string, string>;
export declare const KNOWN_GOOD_CLIENT_PACKAGE_JSON: {
  name: string;
  private: boolean;
  version: string;
  type: string;
  scripts: Record<string, string>;
  dependencies: Record<string, string>;
  devDependencies: Record<string, string>;
};
export declare const KNOWN_GOOD_SERVER_PACKAGE_JSON: {
  name: string;
  version: string;
  main: string;
  scripts: Record<string, string>;
  dependencies: Record<string, string>;
};
export declare const INDEX_HTML: string;
export declare const MAIN_JSX: string;
export declare const VITE_CONFIG_JS: string;
export declare const ROOT_README: string;

export declare function buildExportBundle(rawFiles: Record<string, string>): Record<string, string>;

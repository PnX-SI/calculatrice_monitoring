export interface Indicator {
  id: number;
  name: string;
  description: string;
  protocolId: number;
}

export interface Protocol {
  id: number;
  label: string;
  code: string;
}

export interface SitesGroup {
  id: number;
  name: string;
  nbSites: number;
}

export interface Site {
  id: number;
  name: string;
}

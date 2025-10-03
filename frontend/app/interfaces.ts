export type Indicator = {
  id: number;
  name: string;
  description: string;
  protocolId: number;
};

export type Protocol = {
  id: number;
  label: string;
  code: string;
};

export type SitesGroup = {
  name: string;
  groupId: number;
};

export type Site = {
  id: number;
  name: string;
};

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ConfigService } from '@geonature/services/config.service';
import { ParamsDict } from '@geonature_common/form/data-form.service';
import { from } from 'rxjs';
import {
  Campaign,
  Indicator,
  Protocol,
  Site,
  SitesGroup,
  VisualizationBlockDefinition,
} from '../interfaces';

interface MonitoringSitesGroup {
  id_sites_group: number;
  sites_group_name: string;
  nb_sites: number;
}

interface MonitoringSite {
  id_base_site: number;
  base_site_name: string;
}

interface PaginatedList {
  count: number;
  items: Array<unknown>;
  limit: number;
  page: number;
}

@Injectable()
export class DataService {
  constructor(
    private _http: HttpClient,
    private _config: ConfigService
  ) {}

  getProtocol(protocolId: number) {
    return this._http.get<Protocol>(
      `${this._config.API_ENDPOINT}/calculatrice/protocol/${protocolId}`
    );
  }

  /**
   * Returns the list of available monitoring protocols for the current user.
   *
   * params: parameters are passed as-is as query parameters to the request
   */
  getProtocols(params: ParamsDict) {
    let httpParams = new HttpParams();
    for (const key in params) {
      httpParams = httpParams.set(key, params[key].toString());
    }
    return this._http.get<Array<Protocol>>(`${this._config.API_ENDPOINT}/calculatrice/protocols`, {
      params: httpParams,
    });
  }

  getIndicator(indicatorId: number) {
    return this._http.get<Indicator>(
      `${this._config.API_ENDPOINT}/calculatrice/indicator/${indicatorId}`
    );
  }

  /**
   * Returns the list of indicators associated with the given protocol.
   */
  getIndicators(protocolId: number) {
    return this._http.get<Array<Indicator>>(
      `${this._config.API_ENDPOINT}/calculatrice/indicators?id_protocol=${protocolId}`
    );
  }

  /**
   * Returns the list of sites groups for the given protocol.
   */
  getSitesGroups(protocolCode: string) {
    const url = `${this._config.API_ENDPOINT}/monitorings/refacto/${protocolCode}/sites_groups`;
    const params = {
      sort_dir: 'asc',
      sort: 'sites_group_name',
    };
    function transform(items: Array<MonitoringSitesGroup>): Array<SitesGroup> {
      return items.map<SitesGroup>((item) => ({
        id: item.id_sites_group,
        name: item.sites_group_name,
        nbSites: item.nb_sites,
      }));
    }
    return from(
      this.getAll<MonitoringSitesGroup>(url, params, 'id_sites_group').then((items) =>
        transform(items)
      )
    );
  }

  /**
   * Returns the list of sites for the given protocol and sites group.
   */
  getSites(protocolCode: string, sitesGroup: SitesGroup) {
    const url = `${this._config.API_ENDPOINT}/monitorings/refacto/${protocolCode}/sites`;
    const params = {
      sort_dir: 'asc',
      sort: 'base_site_name',
      id_sites_group: sitesGroup.id,
    };
    function transform(items: Array<MonitoringSite>): Array<Site> {
      return items.map<Site>((item) => ({
        id: item.id_base_site,
        name: item.base_site_name,
      }));
    }
    return from(
      this.getAll<MonitoringSite>(url, params, 'id_base_site').then((items) => transform(items))
    );
  }

  getVisualizationBlocks(
    indicatorId: number,
    sites: Site[],
    campaigns: Campaign[],
    visualizationType: string
  ) {
    return this._http.post<VisualizationBlockDefinition[]>(
      `${this._config.API_ENDPOINT}/calculatrice/indicator/${indicatorId}/visualize`,
      {
        indicator_id: indicatorId,
        sites_ids: sites.map<number>((item) => item.id),
        campaigns: campaigns.map((item) => ({
          start_date: item.startDate,
          end_date: item.endDate,
        })),
        viz_type: visualizationType,
      }
    );
  }

  private async getPage(url: string, params: ParamsDict): Promise<PaginatedList> {
    let httpParams = new HttpParams();
    for (const key in params) {
      httpParams = httpParams.set(key, params[key].toString());
    }
    return this._http.get(url, { params: httpParams }).toPromise() as Promise<PaginatedList>;
  }

  /**
   * Utility method to fetch all pages of a paginated endpoint and return a concatenated list.
   */
  private async getAll<T>(url: string, params: ParamsDict, uniqueKey: string): Promise<Array<T>> {
    const pageSize = 100;
    let page = 1;
    params.page = page;
    params.limit = pageSize;
    const result = await this.getPage(url, params);
    let items = result.items;
    const nbPages = Math.ceil(result.count / pageSize);
    page += 1;
    while (page <= nbPages) {
      params.page = page;
      const nextResult = await this.getPage(url, params);
      nextResult.items.forEach((nextItem) => {
        // We check for unicity in the event where the list changes as we are iterating on the pages
        if (items.findIndex((item) => item[uniqueKey] === nextItem[uniqueKey]) === -1)
          items.push(nextItem);
      });
      page += 1;
    }
    return items as Array<T>;
  }
}

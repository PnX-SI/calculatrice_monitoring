import { Injectable } from '@angular/core';

import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '@geonature/services/config.service';
import { ParamsDict } from '@geonature_common/form/data-form.service';
import { Indicator, Protocol } from '../interfaces';

@Injectable()
export class DataService {
  constructor(
    private _http: HttpClient,
    private _config: ConfigService
  ) {}

  getProtocols(params: ParamsDict) {
    let httpParams = new HttpParams();
    for (const key in params) {
      httpParams = httpParams.set(key, params[key].toString());
    }
    return this._http.get<Array<Protocol>>(`${this._config.API_ENDPOINT}/calculatrice/protocols`, {
      params: httpParams,
    });
  }

  getIndicators(protocolId: number) {
    return this._http.get<Array<Indicator>>(
      `${this._config.API_ENDPOINT}/calculatrice/indicators?id_protocol=${protocolId}`
    );
  }
}

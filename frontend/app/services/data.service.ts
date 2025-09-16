import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';
import { ConfigService } from '@geonature/services/config.service';
import { Indicator, Protocol } from '../interfaces';

@Injectable()
export class DataService {
  constructor(
    private _http: HttpClient,
    private _config: ConfigService
  ) {}

  getProtocols() {
    return this._http.get<Array<Protocol>>(`${this._config.API_ENDPOINT}/calculatrice/protocols`);
  }

  getIndicators(protocolId: number) {
    return this._http.get<Array<Indicator>>(
      `${this._config.API_ENDPOINT}/calculatrice/indicators?id_protocol=${protocolId}`
    );
  }
}

import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatListOption } from '@angular/material/list';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { Indicator, Protocol } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { PermissionService } from '../../services/permission.service';

@Component({
  selector: 'pnx-calc-module',
  templateUrl: './module.component.html',
  styleUrls: ['./module.component.css'],
})
export class ModuleComponent implements OnInit {
  @ViewChild('descriptionModal') protected modalContent: TemplateRef<any>;
  protected indicators: Array<Indicator> = [];
  protected protocols: Array<Protocol> = [];
  protected selectedIndicator: Indicator | undefined;
  protected selectedProtocolId: number | undefined;
  protected isLoadingProtocols = true;
  protected isLoadingIndicators = false;

  constructor(
    private _data: DataService,
    private _modalService: NgbModal,
    private _permissionService: PermissionService,
    private _route: ActivatedRoute,
    private _router: Router
  ) {}

  ngOnInit() {
    this.isLoadingProtocols = true;
    this._data.getProtocols({ with_indicators_only: true }).subscribe({
      next: (data: Array<Protocol>) => {
        this.protocols = data;
        this.isLoadingProtocols = false;
        if (this.protocols.length === 0) {
          return;
        }
        const queryParam = this._route.snapshot.queryParams['protocol'];
        const queryParamId = queryParam ? Number(queryParam) : NaN;
        const savedId = !isNaN(queryParamId) ? queryParamId : this._data.selectedProtocolId;

        const initialProtocol =
          this.protocols.find((protocol) => protocol.id === savedId) || this.protocols[0];
        this.selectProtocol(initialProtocol.id);
      },
      error: () => {
        this.isLoadingProtocols = false;
      },
    });

    this._route.queryParams.subscribe((queryParams) => {
      if (this.protocols.length === 0) {
        return;
      }
      const queryParamId = queryParams['protocol'] ? Number(queryParams['protocol']) : NaN;
      if (!isNaN(queryParamId) && queryParamId !== this.selectedProtocolId) {
        const found = this.protocols.find((protocol) => protocol.id === queryParamId);
        if (found) {
          this.selectProtocol(found.id);
        }
      }
    });
  }

  selectProtocol(protocolId: number) {
    this.selectedProtocolId = protocolId;
    this._data.selectedProtocolId = protocolId;
    this._router.navigate([], {
      relativeTo: this._route,
      queryParams: { protocol: protocolId },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    this.isLoadingIndicators = true;
    this._data.getIndicators(protocolId).subscribe({
      next: (data: Array<Indicator>) => {
        this.indicators = data;
        this.isLoadingIndicators = false;
      },
      error: () => {
        this.isLoadingIndicators = false;
      },
    });
  }

  onProtocolChange(options: MatListOption[]) {
    let protocolId: number = options[0].value;
    this.selectProtocol(protocolId);
  }

  onInformationClick(event: MouseEvent, indicator: Indicator) {
    this.selectedIndicator = indicator;
    this._modalService.open(this.modalContent, { size: 'xl' });

    // Those are to avoid navigating to visualization when clicking for information
    event.preventDefault();
    event.stopPropagation();
  }

  canCreateIndicator(): boolean {
    return this._permissionService.getAdminPermission('C') > 0;
  }

  canEditIndicator(): boolean {
    return this._permissionService.getAdminPermission('U') > 0;
  }

  canReadIndicator(): boolean {
    return this._permissionService.getAdminPermission('R') > 0;
  }

  canReadReferenceTables(): boolean {
    return this._permissionService.getAdminPermission('R') > 0;
  }
}

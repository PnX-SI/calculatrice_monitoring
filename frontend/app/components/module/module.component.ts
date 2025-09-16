import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatListOption } from '@angular/material/list';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { Indicator, Protocol } from '../../interfaces';
import { DataService } from '../../services/data.service';

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

  constructor(
    private _data: DataService,
    private _modalService: NgbModal
  ) {}

  ngOnInit() {
    this._data.getProtocols({ with_indicators_only: true }).subscribe((data: Array<Protocol>) => {
      this.protocols = data;
      this.selectProtocol(this.protocols[0].id);
    });
  }

  selectProtocol(protocolId: number) {
    this._data.getIndicators(protocolId).subscribe((data: Array<Indicator>) => {
      this.indicators = data;
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
}

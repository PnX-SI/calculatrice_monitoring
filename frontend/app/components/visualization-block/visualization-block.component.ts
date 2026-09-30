import { Component, Input, TemplateRef, ViewChild } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { VisualizationBlockDefinition } from '../../interfaces';

@Component({
  selector: 'pnx-calc-visualization-block',
  templateUrl: './visualization-block.component.html',
  styleUrls: ['./visualization-block.component.css'],
})
export class VisualizationBlockComponent {
  @Input() blockDef: VisualizationBlockDefinition;
  @ViewChild('infoModal') protected modalContent: TemplateRef<any>;

  constructor(private _modalService: NgbModal) {}

  onInformationClick() {
    this._modalService.open(this.modalContent, { size: 'xl' });
  }
}

import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { saveAs } from 'file-saver';
import { ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';

@Component({
  selector: 'pnx-calc-reftables',
  templateUrl: './reftables.component.html',
  styleUrls: ['./reftables.component.css'],
})
export class ReferenceTablesComponent implements OnInit {
  protected referenceTables: Array<ReferenceTable> = [];
  protected selectedReferenceTable: ReferenceTable;
  @ViewChild('infoModal') private _infoModalContent: TemplateRef<any>;

  constructor(
    private _data: DataService,
    private _moduleService: ModuleService,
    private _modalService: NgbModal
  ) {}

  ngOnInit() {
    this._data.getReferenceTables().subscribe((data: Array<ReferenceTable>) => {
      this.referenceTables = data;
    });
  }

  showDescription(referenceTable: ReferenceTable) {
    this.selectedReferenceTable = referenceTable;
    this._modalService.open(this._infoModalContent);
  }

  downloadFile(referenceTable: ReferenceTable) {
    this._data.getReferenceTableData(referenceTable).subscribe((result) => {
      saveAs(result, 'reftable.csv');
    });
  }

  toggleActive(referenceTable: ReferenceTable) {
    const toggled = !referenceTable.active;
    this._data.editReferenceTableActiveStatus(referenceTable.id, toggled).subscribe(() => {
      referenceTable.active = toggled;
    });
  }

  private getAdminPerm(perm: string): number {
    return this._moduleService.currentModule.module_objects.CALC_ADMIN_INDICATOR?.cruved[perm] || 0;
  }

  canCreateReferenceTable(): boolean {
    return this.getAdminPerm('C') > 0;
  }

  canEditReferenceTable(): boolean {
    return this.getAdminPerm('U') > 0;
  }

  canExportReferenceTable(): boolean {
    return this.getAdminPerm('E') > 0;
  }

  canDeleteReferenceTable(): boolean {
    return this.getAdminPerm('D') > 0;
  }
}

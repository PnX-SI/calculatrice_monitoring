import { Component, OnInit } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
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

  constructor(
    private _data: DataService,
    private _moduleService: ModuleService
  ) {}

  ngOnInit() {
    this._data.getReferenceTables().subscribe((data: Array<ReferenceTable>) => {
      this.referenceTables = data;
    });
  }

  downloadFile(referenceTable: ReferenceTable) {
    this._data.getReferenceTableData(referenceTable).subscribe((result) => {
      saveAs(result, 'reftable.csv');
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

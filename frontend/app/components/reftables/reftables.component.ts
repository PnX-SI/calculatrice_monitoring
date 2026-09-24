import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { saveAs } from 'file-saver';
import { ToastrService } from 'ngx-toastr';
import { catchError } from 'rxjs/operators';
import { ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-reftables',
  templateUrl: './reftables.component.html',
  styleUrls: ['./reftables.component.css'],
})
export class ReferenceTablesComponent implements OnInit {
  protected referenceTables: Array<ReferenceTable> = [];
  protected selectedReferenceTable: ReferenceTable;
  @ViewChild('infoModal') private _infoModalContent: TemplateRef<any>;
  @ViewChild('deleteConfirmModal') private _deleteConfirmModalContent: TemplateRef<any>;

  constructor(
    private _data: DataService,
    private _moduleService: ModuleService,
    private _modalService: NgbModal,
    private _utils: UtilsService,
    private _toastr: ToastrService
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

  confirmDeleteReferenceTable(referenceTable: ReferenceTable) {
    this.selectedReferenceTable = referenceTable;
    this._modalService.open(this._deleteConfirmModalContent).result.then(
      (result) => {
        if (result === 'confirm') {
          this._deleteReferenceTable(referenceTable);
        }
      },
      () => {}
    );
  }

  private _deleteReferenceTable(referenceTable: ReferenceTable) {
    this._data
      .deleteReferenceTable(referenceTable.id)
      .pipe(catchError((error: HttpErrorResponse) => this._handleDeleteError(error)))
      .subscribe(() => {
        this.referenceTables = this.referenceTables.filter((rt) => rt.id !== referenceTable.id);
      });
  }

  private _handleDeleteError(error: HttpErrorResponse) {
    if (error.error) {
      Object.keys(error.error).forEach((key) => {
        const message = Array.isArray(error.error[key]) ? error.error[key][0] : error.error[key];
        this._toastr.error(message, 'Erreur', {
          disableTimeOut: true,
          tapToDismiss: false,
          closeButton: true,
          easeTime: 0,
        });
      });
    } else {
      this._toastr.error(
        'Une erreur est survenue lors de la suppression du tableau de référence.',
        'Erreur',
        { disableTimeOut: true, tapToDismiss: false, closeButton: true, easeTime: 0 }
      );
    }
    return this._utils.handleError(error);
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

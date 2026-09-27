import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IndicatorDetails } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { PermissionService } from '../../services/permission.service';

@Component({
  selector: 'pnx-calc-indicator',
  templateUrl: './indicator-details.component.html',
  styleUrls: ['./indicator-details.component.css'],
})
export class IndicatorDetailsComponent implements OnInit {
  protected indicatorDetails: IndicatorDetails | undefined;

  constructor(
    private _data: DataService,
    private _route: ActivatedRoute,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this._route.params.subscribe((params) => {
      const indicatorId: number = params.indicatorId;
      this._data.getIndicatorDetails(indicatorId).subscribe((data: IndicatorDetails) => {
        this.indicatorDetails = data;
      });
    });
  }

  canEditIndicator(): boolean {
    return this._permissionService.getAdminPermission('U') > 0;
  }
}
